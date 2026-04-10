// ============================================================
// alert.rs — Anomaly detection & threat rules engine
//
// Rules implemented:
//   1. Port Scan      — 1 src → 15+ unique dst ports in window
//   2. SYN Flood      — 200+ SYNs without ACK from one src
//   3. DDoS Flood     — Exceeds pps_threshold from one src
//   4. ICMP Flood     — Excessive ICMP from one source
//   5. Unusual Port   — Traffic on known malicious ports
// ============================================================

use ahash::AHashMap;
use chrono::Local;
use parking_lot::RwLock;
use std::sync::Arc;
use tokio::sync::mpsc::Receiver;

use crate::tracker::ConnectionTracker;
use crate::types::{AlertEvent, AlertKind, AlertSeverity, AppState, ParsedPacket};

// Ports known to be suspicious / commonly attacked
const SUSPICIOUS_PORTS: &[u16] = &[
    4444, 1337, 31337, // Common backdoor/C2 ports
    6666, 6667, 6668,  // IRC (often used by botnets)
    9001, 9030,        // Tor default ports
    5900,              // VNC
    3389,              // RDP (external exposure)
    23,                // Telnet (unencrypted)
    2323,              // Alt Telnet
];

pub struct AlertEngine {
    // Dedup: don't fire same alert twice within 5 seconds
    last_fired: AHashMap<String, std::time::Instant>,
}

impl AlertEngine {
    pub fn new() -> Self {
        Self {
            last_fired: AHashMap::new(),
        }
    }

    /// Analyze a packet and return any triggered alerts
    pub fn analyze(
        &mut self,
        pkt: &ParsedPacket,
        tracker: &ConnectionTracker,
    ) -> Option<Vec<AlertEvent>> {
        let mut alerts = Vec::new();

        // ── Rule 1: Port Scan ───────────────────────────────
        let unique_ports = tracker.unique_ports_for(&pkt.src_ip);
        if unique_ports >= 15 {
            if self.can_fire(&format!("scan:{}", pkt.src_ip)) {
                alerts.push(AlertEvent {
                    timestamp: Local::now(),
                    severity: AlertSeverity::High,
                    kind: AlertKind::PortScan,
                    src_ip: pkt.src_ip.clone(),
                    message: format!(
                        "Port scan: {} contacted {} unique ports",
                        pkt.src_ip, unique_ports
                    ),
                });
            }
        }

        // ── Rule 2: SYN Flood ───────────────────────────────
        if pkt.flags.syn && !pkt.flags.ack {
            let syn_count = tracker.syn_count_for(&pkt.src_ip);
            if syn_count > 200 {
                if self.can_fire(&format!("syn:{}", pkt.src_ip)) {
                    alerts.push(AlertEvent {
                        timestamp: Local::now(),
                        severity: AlertSeverity::Critical,
                        kind: AlertKind::SynFlood,
                        src_ip: pkt.src_ip.clone(),
                        message: format!(
                            "SYN flood: {} sent {} SYN packets",
                            pkt.src_ip, syn_count
                        ),
                    });
                }
            }
        }

        // ── Rule 3: ICMP Flood ──────────────────────────────
        if pkt.protocol.starts_with("ICMP") {
            let syn_count = tracker.syn_count_for(&pkt.src_ip);
            if syn_count > 500 {
                if self.can_fire(&format!("icmp:{}", pkt.src_ip)) {
                    alerts.push(AlertEvent {
                        timestamp: Local::now(),
                        severity: AlertSeverity::High,
                        kind: AlertKind::IcmpFlood,
                        src_ip: pkt.src_ip.clone(),
                        message: format!("ICMP flood from {}", pkt.src_ip),
                    });
                }
            }
        }

        // ── Rule 4: Suspicious Port ─────────────────────────
        let dst_port = pkt.dst_port.unwrap_or(0);
        if SUSPICIOUS_PORTS.contains(&dst_port) {
            if self.can_fire(&format!("port:{}:{}", pkt.src_ip, dst_port)) {
                alerts.push(AlertEvent {
                    timestamp: Local::now(),
                    severity: AlertSeverity::Medium,
                    kind: AlertKind::UnusualPort,
                    src_ip: pkt.src_ip.clone(),
                    message: format!(
                        "Traffic to suspicious port {} from {}",
                        dst_port, pkt.src_ip
                    ),
                });
            }
        }

        if alerts.is_empty() {
            None
        } else {
            Some(alerts)
        }
    }

    /// Rate-limit alert firing: same key can only fire once every 5 seconds
    fn can_fire(&mut self, key: &str) -> bool {
        let now = std::time::Instant::now();
        if let Some(last) = self.last_fired.get(key) {
            if now.duration_since(*last).as_secs() < 5 {
                return false;
            }
        }
        self.last_fired.insert(key.to_string(), now);
        true
    }
}

/// Receives AlertEvents and writes them into AppState
pub async fn process_alerts(
    mut rx: Receiver<AlertEvent>,
    state: Arc<RwLock<AppState>>,
) {
    while let Some(alert) = rx.recv().await {
        let mut s = state.write();
        // Keep last 100 alerts
        if s.alerts.len() >= 100 {
            s.alerts.pop_front();
        }
        s.alerts.push_back(alert);
    }
}

/// Plain-text alert printer for --no-tui mode
pub async fn print_alerts(mut rx: Receiver<AlertEvent>) {
    while let Some(alert) = rx.recv().await {
        let color = match alert.severity {
            AlertSeverity::Critical => "\x1b[1;31m",
            AlertSeverity::High => "\x1b[0;31m",
            AlertSeverity::Medium => "\x1b[0;33m",
            AlertSeverity::Low => "\x1b[0;36m",
        };
        eprintln!(
            "{}⚠  [{}] {} | {} | {}\x1b[0m",
            color,
            alert.timestamp.format("%H:%M:%S"),
            alert.severity,
            alert.kind,
            alert.message
        );
    }
}