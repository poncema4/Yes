// ============================================================
// capture.rs — Raw packet capture via pnet_datalink
//
// This module opens a raw socket on the specified interface
// and forwards raw Ethernet frames into our async pipeline
// via an mpsc channel.
//
// Requires root/Administrator privileges to open raw sockets.
// ============================================================

use pnet::datalink::{self, Channel::Ethernet, Config};
use tokio::sync::mpsc::Sender;

/// Find a network interface by name, panic with a helpful message if missing
fn find_interface(name: &str) -> pnet::datalink::NetworkInterface {
    datalink::interfaces()
        .into_iter()
        .find(|iface| iface.name == name)
        .unwrap_or_else(|| {
            eprintln!("\n❌ Interface '{}' not found.\n", name);
            eprintln!("Available interfaces:");
            for iface in datalink::interfaces() {
                let ips: Vec<_> = iface.ips.iter().map(|ip| ip.to_string()).collect();
                eprintln!("  {} — {}", iface.name, ips.join(", "));
            }
            eprintln!("\nRe-run with: --interface <name>");
            std::process::exit(1);
        })
}

/// Blocking capture loop — run this on a dedicated OS thread!
/// Sends raw frame bytes into the pipeline channel.
pub fn capture_packets(interface_name: &str, tx: Sender<Vec<u8>>) {
    let interface = find_interface(interface_name);

    // pnet channel config — 4 MB ring buffer
    let config = Config {
        read_buffer_size: 4 * 1024 * 1024,
        write_buffer_size: 4096,
        ..Default::default()
    };

    let (_, mut receiver) = match datalink::channel(&interface, config) {
        Ok(Ethernet(tx_chan, rx_chan)) => (tx_chan, rx_chan),
        Ok(_) => {
            eprintln!("❌ Unsupported channel type (not Ethernet)");
            return;
        }
        Err(e) => {
            eprintln!("❌ Failed to open capture channel on {}: {}", interface_name, e);
            eprintln!("   → Are you running as root/sudo?");
            return;
        }
    };

    eprintln!("✅ Capture started on '{}'", interface_name);

    loop {
        match receiver.next() {
            Ok(packet) => {
                // Clone the raw bytes and send to pipeline
                // If the channel is full (backpressure), drop the frame rather than block
                let bytes = packet.to_vec();
                if tx.blocking_send(bytes).is_err() {
                    // Receiver dropped — pipeline shut down, exit
                    break;
                }
            }
            Err(e) => {
                // Transient read errors are normal (e.g., signal interrupts)
                eprintln!("⚠️  Capture read error: {}", e);
            }
        }
    }
}

/// List available interfaces (used by --list-interfaces flag)
pub fn list_interfaces() {
    println!("{:<20} {:<40} {:<10}", "NAME", "IPs", "FLAGS");
    println!("{}", "-".repeat(72));
    for iface in datalink::interfaces() {
        let ips: Vec<_> = iface.ips.iter().map(|ip| ip.to_string()).collect();
        let flags = format!(
            "{}{}{}",
            if iface.is_up() { "UP " } else { "   " },
            if iface.is_loopback() { "LO " } else { "   " },
            if iface.is_broadcast() { "BC" } else { "  " }
        );
        println!(
            "{:<20} {:<40} {}",
            iface.name,
            ips.join(", "),
            flags
        );
    }
}