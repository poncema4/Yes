mod alert;
mod capture;
mod parser;
mod pipeline;
mod tracker;
mod tui;
mod types;

use clap::Parser;
use parking_lot::RwLock;
use std::sync::Arc;
use tokio::sync::mpsc;

use crate::types::{AppState, SnifferConfig};

/// Advanced Rust Network Packet Analyzer with Live TUI
#[derive(Parser, Debug, Clone)]
#[command(name = "sniffer", about = "Advanced Rust Packet Sniffer", version)]
pub struct Cli {
    /// Network interface to capture on (e.g. eth0, wlan0, en0)
    #[arg(short, long, default_value = "lo")]
    pub interface: String,

    /// Protocol filter: "tcp", "udp", "icmp", or "all"
    #[arg(short, long, default_value = "all")]
    pub filter: String,

    /// Max packets to capture (0 = unlimited)
    #[arg(short = 'n', long, default_value_t = 0)]
    pub count: usize,

    /// Write captured packets to JSON file
    #[arg(short, long)]
    pub output: Option<String>,

    /// Show hex payload dump in logs
    #[arg(short, long)]
    pub verbose: bool,

    /// Watch a specific port (e.g. 80, 443, 22)
    #[arg(short, long)]
    pub port: Option<u16>,

    /// Disable TUI — plain terminal output mode
    #[arg(long)]
    pub no_tui: bool,

    /// Packets-per-second alert threshold per source IP (default: 100)
    #[arg(long, default_value_t = 100)]
    pub pps_threshold: u64,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    // ── Shared state ─────────────────────────────────────────
    // Arc<RwLock<T>> lets the capture thread, pipeline, and TUI
    // all read/write the same AppState without unsafe code.
    let state: Arc<RwLock<AppState>> = Arc::new(RwLock::new(AppState::new()));

    // ── Channels ─────────────────────────────────────────────
    // raw_tx/rx  : raw Ethernet frames  (capture → pipeline)
    // alert_tx/rx: triggered alerts     (pipeline → alert sink)
    let (raw_tx, raw_rx) = mpsc::channel::<Vec<u8>>(4096);
    let (alert_tx, alert_rx) = mpsc::channel::<types::AlertEvent>(256);

    let config = SnifferConfig {
        interface: cli.interface.clone(),
        filter: cli.filter.clone(),
        max_packets: cli.count,
        output_file: cli.output.clone(),
        verbose: cli.verbose,
        watch_port: cli.port,
        pps_threshold: cli.pps_threshold,
    };

    eprintln!(
        "\n rust_packet_sniffer | iface: {} | filter: {} | threshold: {} pps\n",
        cli.interface, cli.filter, cli.pps_threshold
    );

    // ── Capture thread ───────────────────────────────────────
    // pnet's receive loop is synchronous/blocking, so it MUST
    // live on its own OS thread — never inside a tokio task.
    let iface = cli.interface.clone();
    std::thread::spawn(move || {
        capture::capture_packets(&iface, raw_tx);
    });

    // ── Pipeline task ────────────────────────────────────────
    // Async: receives raw frames, parses, tracks, fires alerts
    let state_pipeline = Arc::clone(&state);
    let cfg_pipeline = config.clone();
    tokio::spawn(async move {
        pipeline::run(raw_rx, alert_tx, state_pipeline, cfg_pipeline).await;
    });

    // ── Alert sink task ──────────────────────────────────────
    // Receives AlertEvents from pipeline, writes them to state
    let state_alerts = Arc::clone(&state);
    tokio::spawn(async move {
        alert::process_alerts(alert_rx, state_alerts).await;
    });

    // ── UI ───────────────────────────────────────────────────
    if cli.no_tui {
        // Plain mode: print stats + recent packets to stdout
        loop {
            tokio::time::sleep(std::time::Duration::from_secs(1)).await;
            let s = state.read();
            println!(
                "[{}] {} pkts | {} bytes | {} flows | {} alerts",
                chrono::Local::now().format("%H:%M:%S"),
                s.total_packets,
                s.total_bytes,
                s.connections.len(),
                s.alerts.len()
            );
            for pkt in s.recent_packets.iter().rev().take(5) {
                println!("  {}", pkt.summary());
            }
            println!();
        }
    } else {
        // Full TUI dashboard (ratatui + crossterm)
        tui::run_tui(Arc::clone(&state)).await?;
    }

    Ok(())
}