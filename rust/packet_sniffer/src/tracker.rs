// ============================================================
// tracker.rs — Connection state machine & flow tracking
//
// Tracks per-flow (5-tuple) state:
//   src_ip:src_port → dst_ip:dst_port (proto)
//
// Also maintains per-source IP rate counters for threat detection.
// ============================================================

use ahash::AHashMap;
use chrono::Local;
use std::time::{Duration, Instant};

use crate::types::{ConnectionState, FlowEntry, ParsedPacket};

/// Per-source IP rate tracking for DDoS/flood detection
#[derive(Debug)]
struct SourceStats {
    packets: u64,
    bytes: u64,
    unique_dst_ports: std::collections::HashSet<u16>,
    window_start: Instant,
    syn_count: u64,
}

impl SourceStats {
    fn new() -> Self {
        Self {
            packets: 0,
            bytes: 0,
            unique_dst_ports: std::collections::HashSet::new(),
            window_start: Instant::now(),
            syn_count: 0,
        }
    }
}

pub struct ConnectionTracker {
    flows: AHashMap<String, FlowEntry>,
    source_stats: AHashMap<String, SourceStats>,
    pps_threshold: u64,
    flow_timeout: Duration,
}

impl ConnectionTracker {
    pub fn new(pps_threshold: u64) -> Self {
        Self {
            flows: AHashMap::new(),
            source_stats: AHashMap::new(),
            pps_threshold,
            flow_timeout: Duration::from_secs(120), // 2 min idle timeout
        }
    }

    /// Process a packet, update or create flow entry.
    /// Returns the updated FlowEntry.
    pub fn update(&mut self, pkt: &ParsedPacket) -> Option<FlowEntry> {
        let src_port = pkt.src_port.unwrap_or(0);
        let dst_port = pkt.dst_port.unwrap_or(0);

        // 5-tuple flow key
        let key = format!(
            "{}:{}:{}→{}:{}",
            pkt.protocol, pkt.src_ip, src_port, pkt.dst_ip, dst_port
        );

        let now = Local::now();

        let flow = self.flows.entry(key.clone()).or_insert_with(|| FlowEntry {
            key: key.clone(),
            src: pkt.src_ip.clone(),
            dst: pkt.dst_ip.clone(),
            protocol: pkt.protocol.clone(),
            src_port,
            dst_port,
            packet_count: 0,
            byte_count: 0,
            state: if pkt.flags.syn && !pkt.flags.ack {
                ConnectionState::SynSent
            } else {
                ConnectionState::Unknown
            },
            first_seen: now,
            last_seen: now,
            flags_seen: String::new(),
        });

        flow.packet_count += 1;
        flow.byte_count += pkt.length as u64;
        flow.last_seen = now;

        // State machine transitions
        flow.state = match flow.state {
            ConnectionState::SynSent if pkt.flags.ack => ConnectionState::Established,
            ConnectionState::Established if pkt.flags.fin => ConnectionState::FinWait,
            ConnectionState::FinWait if pkt.flags.ack => ConnectionState::Closed,
            ConnectionState::Established if pkt.flags.rst => ConnectionState::Closed,
            ref s => s.clone(),
        };

        // Track flags observed on this flow
        let flag_char = pkt.flag_str();
        if !flow.flags_seen.contains(&flag_char) {
            flow.flags_seen.push_str(&flag_char);
        }

        // Update per-source stats (for anomaly detection)
        let stats = self.source_stats.entry(pkt.src_ip.clone()).or_insert_with(SourceStats::new);
        stats.packets += 1;
        stats.bytes += pkt.length as u64;
        if pkt.flags.syn && !pkt.flags.ack {
            stats.syn_count += 1;
        }
        if dst_port > 0 {
            stats.unique_dst_ports.insert(dst_port);
        }

        Some(flow.clone())
    }

    /// Packets per second for a given source IP (over last 1s window)
    pub fn pps_for(&mut self, src: &str) -> u64 {
        if let Some(stats) = self.source_stats.get_mut(src) {
            let elapsed = stats.window_start.elapsed().as_secs_f64();
            if elapsed > 0.0 {
                return (stats.packets as f64 / elapsed) as u64;
            }
        }
        0
    }

    /// Number of unique destination ports contacted by this source
    pub fn unique_ports_for(&self, src: &str) -> usize {
        self.source_stats
            .get(src)
            .map(|s| s.unique_dst_ports.len())
            .unwrap_or(0)
    }

    /// SYN count for this source (used for SYN flood detection)
    pub fn syn_count_for(&self, src: &str) -> u64 {
        self.source_stats
            .get(src)
            .map(|s| s.syn_count)
            .unwrap_or(0)
    }

    pub fn pps_threshold(&self) -> u64 {
        self.pps_threshold
    }

    /// Remove flows idle longer than the timeout
    pub fn evict_expired(&self, connections: &mut AHashMap<String, FlowEntry>) {
        let now = Local::now();
        let timeout_secs = self.flow_timeout.as_secs() as i64;
        connections.retain(|_, flow| {
            (now - flow.last_seen).num_seconds() < timeout_secs
        });
    }
}