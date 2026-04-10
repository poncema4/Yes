// ============================================================
// types.rs — Shared data structures across all modules
// ============================================================

use ahash::AHashMap;
use chrono::{DateTime, Local};
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;

/// Global application state — shared between capture, pipeline, and TUI
#[derive(Debug)]
pub struct AppState {
    pub total_packets: u64,
    pub total_bytes: u64,
    pub protocol_counts: AHashMap<String, u64>,
    pub connections: AHashMap<String, FlowEntry>,
    pub recent_packets: VecDeque<ParsedPacket>,
    pub alerts: VecDeque<AlertEvent>,
    pub top_talkers: Vec<(String, u64)>, // (ip, bytes)
    pub bytes_per_second: u64,
    pub packets_per_second: u64,
    pub start_time: DateTime<Local>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            total_packets: 0,
            total_bytes: 0,
            protocol_counts: AHashMap::new(),
            connections: AHashMap::new(),
            recent_packets: VecDeque::new(),
            alerts: VecDeque::new(),
            top_talkers: Vec::new(),
            bytes_per_second: 0,
            packets_per_second: 0,
            start_time: Local::now(),
        }
    }
}

/// A fully parsed network packet
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedPacket {
    pub timestamp: String,
    pub src_ip: String,
    pub dst_ip: String,
    pub src_port: Option<u16>,
    pub dst_port: Option<u16>,
    pub protocol: String,
    pub length: usize,
    pub ttl: u8,
    pub flags: PacketFlags,
    pub payload_preview: String, // First 32 bytes as hex
}

impl ParsedPacket {
    pub fn summary(&self) -> String {
        let ports = match (self.src_port, self.dst_port) {
            (Some(s), Some(d)) => format!(":{}→:{}", s, d),
            _ => String::new(),
        };
        format!(
            "[{}] {} {} → {} {} {} {} bytes",
            self.timestamp,
            self.protocol,
            self.src_ip,
            self.dst_ip,
            ports,
            self.flag_str(),
            self.length
        )
    }

    pub fn flag_str(&self) -> String {
        let mut f = String::new();
        if self.flags.syn { f.push('S'); }
        if self.flags.ack { f.push('A'); }
        if self.flags.fin { f.push('F'); }
        if self.flags.rst { f.push('R'); }
        if self.flags.psh { f.push('P'); }
        if self.flags.urg { f.push('U'); }
        if f.is_empty() { ".".into() } else { format!("[{}]", f) }
    }
}

/// TCP flag breakdown
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PacketFlags {
    pub syn: bool,
    pub ack: bool,
    pub fin: bool,
    pub rst: bool,
    pub psh: bool,
    pub urg: bool,
}

/// A tracked network flow / connection
#[derive(Debug, Clone)]
pub struct FlowEntry {
    pub key: String, // "proto:srcIP:srcPort→dstIP:dstPort"
    pub src: String,
    pub dst: String,
    pub protocol: String,
    pub src_port: u16,
    pub dst_port: u16,
    pub packet_count: u64,
    pub byte_count: u64,
    pub state: ConnectionState,
    pub first_seen: DateTime<Local>,
    pub last_seen: DateTime<Local>,
    pub flags_seen: String,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ConnectionState {
    SynSent,
    Established,
    FinWait,
    Closed,
    Unknown,
}

impl std::fmt::Display for ConnectionState {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::SynSent => write!(f, "SYN_SENT"),
            Self::Established => write!(f, "ESTABLISHED"),
            Self::FinWait => write!(f, "FIN_WAIT"),
            Self::Closed => write!(f, "CLOSED"),
            Self::Unknown => write!(f, "UNKNOWN"),
        }
    }
}

/// Anomaly / threat alert
#[derive(Debug, Clone)]
pub struct AlertEvent {
    pub timestamp: DateTime<Local>,
    pub severity: AlertSeverity,
    pub kind: AlertKind,
    pub src_ip: String,
    pub message: String,
}

#[derive(Debug, Clone, PartialEq)]
pub enum AlertSeverity {
    Low,
    Medium,
    High,
    Critical,
}

impl std::fmt::Display for AlertSeverity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Low => write!(f, "LOW"),
            Self::Medium => write!(f, "MED"),
            Self::High => write!(f, "HIGH"),
            Self::Critical => write!(f, "CRIT"),
        }
    }
}

#[derive(Debug, Clone)]
pub enum AlertKind {
    PortScan,       // Many dsts from one src
    DDoSFlood,      // Extreme pps from one src
    SynFlood,       // Many SYN no ACK
    UnusualPort,    // Traffic on suspicious port
    LargeBurst,     // Sudden packet burst
    IcmpFlood,      // ICMP flood
}

impl std::fmt::Display for AlertKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::PortScan => write!(f, "PORT_SCAN"),
            Self::DDoSFlood => write!(f, "DDOS_FLOOD"),
            Self::SynFlood => write!(f, "SYN_FLOOD"),
            Self::UnusualPort => write!(f, "UNUSUAL_PORT"),
            Self::LargeBurst => write!(f, "LARGE_BURST"),
            Self::IcmpFlood => write!(f, "ICMP_FLOOD"),
        }
    }
}

/// Config passed from CLI to all subsystems
#[derive(Debug, Clone)]
pub struct SnifferConfig {
    pub interface: String,
    pub filter: String,
    pub max_packets: usize,
    pub output_file: Option<String>,
    pub verbose: bool,
    pub watch_port: Option<u16>,
    pub pps_threshold: u64,
}