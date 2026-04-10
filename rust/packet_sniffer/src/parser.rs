// ============================================================
// parser.rs — Packet dissection: Ethernet → IP → TCP/UDP/ICMP
//
// Layers parsed:
//   Layer 2: Ethernet (EtherType detection)
//   Layer 3: IPv4 (TTL, src/dst, protocol)
//   Layer 4: TCP (ports, flags, seq/ack)
//             UDP (ports, length)
//             ICMP (type, code)
// ============================================================

use chrono::Local;
use pnet::packet::ethernet::{EtherTypes, EthernetPacket};
use pnet::packet::icmp::IcmpPacket;
use pnet::packet::ip::IpNextHeaderProtocols;
use pnet::packet::ipv4::Ipv4Packet;
use pnet::packet::tcp::TcpPacket;
use pnet::packet::udp::UdpPacket;
use pnet::packet::Packet;

use crate::types::{PacketFlags, ParsedPacket};

/// Parse a raw Ethernet frame into a structured ParsedPacket.
/// Returns None if the frame is not IPv4 or is malformed.
pub fn parse_packet(raw: &[u8]) -> Option<ParsedPacket> {
    let eth = EthernetPacket::new(raw)?;

    match eth.get_ethertype() {
        EtherTypes::Ipv4 => parse_ipv4(eth.payload()),
        // Future: EtherTypes::Ipv6 => parse_ipv6(eth.payload()),
        // Future: EtherTypes::Arp  => parse_arp(eth.payload()),
        _ => None,
    }
}

/// Dissect an IPv4 datagram
fn parse_ipv4(data: &[u8]) -> Option<ParsedPacket> {
    let ip = Ipv4Packet::new(data)?;
    let src_ip = ip.get_source().to_string();
    let dst_ip = ip.get_destination().to_string();
    let ttl = ip.get_ttl();
    let total_len = ip.get_total_length() as usize;
    let timestamp = Local::now().format("%H:%M:%S%.3f").to_string();

    match ip.get_next_level_protocol() {
        IpNextHeaderProtocols::Tcp => {
            let tcp = TcpPacket::new(ip.payload())?;
            let flags = PacketFlags {
                syn: tcp.get_flags() & 0b0000_0010 != 0,
                ack: tcp.get_flags() & 0b0001_0000 != 0,
                fin: tcp.get_flags() & 0b0000_0001 != 0,
                rst: tcp.get_flags() & 0b0000_0100 != 0,
                psh: tcp.get_flags() & 0b0000_1000 != 0,
                urg: tcp.get_flags() & 0b0010_0000 != 0,
            };
            Some(ParsedPacket {
                timestamp,
                src_ip,
                dst_ip,
                src_port: Some(tcp.get_source()),
                dst_port: Some(tcp.get_destination()),
                protocol: "TCP".into(),
                length: total_len,
                ttl,
                flags,
                payload_preview: hex_preview(tcp.payload()),
            })
        }

        IpNextHeaderProtocols::Udp => {
            let udp = UdpPacket::new(ip.payload())?;
            Some(ParsedPacket {
                timestamp,
                src_ip,
                dst_ip,
                src_port: Some(udp.get_source()),
                dst_port: Some(udp.get_destination()),
                protocol: "UDP".into(),
                length: total_len,
                ttl,
                flags: PacketFlags::default(),
                payload_preview: hex_preview(udp.payload()),
            })
        }

        IpNextHeaderProtocols::Icmp => {
            let icmp = IcmpPacket::new(ip.payload())?;
            let type_code = format!(
                "T{}C{}",
                icmp.get_icmp_type().0,
                icmp.get_icmp_code().0
            );
            Some(ParsedPacket {
                timestamp,
                src_ip,
                dst_ip,
                src_port: None,
                dst_port: None,
                protocol: format!("ICMP({})", type_code),
                length: total_len,
                ttl,
                flags: PacketFlags::default(),
                payload_preview: hex_preview(ip.payload()),
            })
        }

        other => {
            // Still record unknown IPv4 protocols (ESP, GRE, etc.)
            Some(ParsedPacket {
                timestamp,
                src_ip,
                dst_ip,
                src_port: None,
                dst_port: None,
                protocol: format!("IP({})", other.0),
                length: total_len,
                ttl,
                flags: PacketFlags::default(),
                payload_preview: hex_preview(ip.payload()),
            })
        }
    }
}

/// First 32 bytes of payload formatted as space-separated hex pairs
fn hex_preview(data: &[u8]) -> String {
    data.iter()
        .take(32)
        .map(|b| format!("{:02x}", b))
        .collect::<Vec<_>>()
        .join(" ")
}

/// Map well-known port numbers to service names
pub fn port_service(port: u16) -> &'static str {
    match port {
        20 | 21 => "FTP",
        22 => "SSH",
        23 => "Telnet",
        25 => "SMTP",
        53 => "DNS",
        67 | 68 => "DHCP",
        80 => "HTTP",
        110 => "POP3",
        143 => "IMAP",
        443 => "HTTPS",
        3306 => "MySQL",
        5432 => "PostgreSQL",
        6379 => "Redis",
        8080 => "HTTP-Alt",
        8443 => "HTTPS-Alt",
        27017 => "MongoDB",
        _ => "?",
    }
}