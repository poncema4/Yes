// ============================================================
// pipeline.rs — Async packet processing pipeline
//   raw bytes → parse → track → alert → state update
// ============================================================

use parking_lot::RwLock;
use std::sync::Arc;
use tokio::sync::mpsc;

use crate::alert::AlertEngine;
use crate::parser;
use crate::tracker::ConnectionTracker;
use crate::types::{AlertEvent, AppState, SnifferConfig};

pub async fn run(
    mut rx: mpsc::Receiver<Vec<u8>>,
    alert_tx: mpsc::Sender<AlertEvent>,
    state: Arc<RwLock<AppState>>,
    config: SnifferConfig,
) {
    let mut tracker = ConnectionTracker::new(config.pps_threshold);
    let mut alert_engine = AlertEngine::new();
    let mut packet_count = 0usize;

    while let Some(raw) = rx.recv().await {
        let Some(pkt) = parser::parse_packet(&raw) else {
            continue;
        };

        // Apply protocol filter
        let proto_lower = pkt.protocol.to_lowercase();
        let filter = config.filter.to_lowercase();
        if filter != "all" && !proto_lower.starts_with(&filter) {
            continue;
        }

        // Apply port filter if set
        if let Some(watch_port) = config.watch_port {
            if pkt.src_port != Some(watch_port) && pkt.dst_port != Some(watch_port) {
                continue;
            }
        }

        // Verbose hex dump
        if config.verbose {
            eprintln!("  HEX: {}", pkt.payload_preview);
        }

        // Update global stats
        {
            let mut s = state.write();
            s.total_packets += 1;
            s.total_bytes += pkt.length as u64;
            *s.protocol_counts.entry(pkt.protocol.clone()).or_insert(0) += 1;

            // Rolling window: keep last 200 packets
            if s.recent_packets.len() >= 200 {
                s.recent_packets.pop_front();
            }
            s.recent_packets.push_back(pkt.clone());
        }

        // Track flow
        let flow = tracker.update(&pkt);
        {
            let mut s = state.write();
            if let Some(f) = flow {
                s.connections.insert(f.key.clone(), f);
            }
            // Periodic eviction of stale flows
            if s.total_packets % 500 == 0 {
                tracker.evict_expired(&mut s.connections);

                // Rebuild top-talkers list from connection map
                let mut talkers: Vec<(String, u64)> = s
                    .connections
                    .values()
                    .map(|f| (f.src.clone(), f.byte_count))
                    .fold(
                        std::collections::HashMap::new(),
                        |mut acc, (ip, bytes)| {
                            *acc.entry(ip).or_insert(0) += bytes;
                            acc
                        },
                    )
                    .into_iter()
                    .collect();
                talkers.sort_by(|a, b| b.1.cmp(&a.1));
                talkers.truncate(10);
                s.top_talkers = talkers;
            }
        }

        // Run anomaly detection rules
        if let Some(alerts) = alert_engine.analyze(&pkt, &tracker) {
            for a in alerts {
                let _ = alert_tx.send(a).await;
            }
        }

        packet_count += 1;
        if config.max_packets > 0 && packet_count >= config.max_packets {
            eprintln!("Reached max packet count ({}), stopping.", config.max_packets);
            break;
        }
    }
}