// ============================================================
// tui.rs — Live terminal dashboard using ratatui + crossterm
//
// Layout:
//   ┌─────────────────────────────────────────────────────────┐
//   │  Header: interface info + global counters               │
//   ├──────────────────┬──────────────────┬───────────────────┤
//   │  Protocol Chart  │  Top Talkers     │  Active Flows     │
//   ├──────────────────┴──────────────────┴───────────────────┤
//   │  Recent Packets (scrolling log)                         │
//   ├─────────────────────────────────────────────────────────┤
//   │  Alerts                                                 │
//   └─────────────────────────────────────────────────────────┘
//
// Keybindings:
//   q / Ctrl-C  — quit
//   Tab         — switch focus (packets / connections / alerts)
//   ↑↓          — scroll selected pane
// ============================================================

use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyModifiers},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use parking_lot::RwLock;
use ratatui::{
    backend::CrosstermBackend,
    layout::{Alignment, Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{
        BarChart, Block, Borders, Cell, Gauge, List, ListItem, Paragraph, Row, Table, Tabs, Wrap,
    },
    Frame, Terminal,
};
use std::{
    io,
    sync::Arc,
    time::{Duration, Instant},
};

use crate::types::{AlertSeverity, AppState};

#[derive(PartialEq)]
enum Tab {
    Dashboard,
    Connections,
    Alerts,
}

struct TuiState {
    tab: Tab,
    packet_scroll: usize,
    conn_scroll: usize,
    alert_scroll: usize,
    last_pkt_count: u64,
    last_byte_count: u64,
    rate_ts: Instant,
}

impl TuiState {
    fn new() -> Self {
        Self {
            tab: Tab::Dashboard,
            packet_scroll: 0,
            conn_scroll: 0,
            alert_scroll: 0,
            last_pkt_count: 0,
            last_byte_count: 0,
            rate_ts: Instant::now(),
        }
    }
}

pub async fn run_tui(state: Arc<RwLock<AppState>>) -> Result<(), Box<dyn std::error::Error>> {
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut ui_state = TuiState::new();
    let tick_rate = Duration::from_millis(200); // 5 FPS — low enough to be smooth
    let mut last_tick = Instant::now();

    loop {
        terminal.draw(|f| render(f, &state, &mut ui_state))?;

        let timeout = tick_rate.saturating_sub(last_tick.elapsed());
        if event::poll(timeout)? {
            if let Event::Key(key) = event::read()? {
                match (key.modifiers, key.code) {
                    (KeyModifiers::CONTROL, KeyCode::Char('c')) | (_, KeyCode::Char('q')) => {
                        break;
                    }
                    (_, KeyCode::Tab) => {
                        ui_state.tab = match ui_state.tab {
                            Tab::Dashboard => Tab::Connections,
                            Tab::Connections => Tab::Alerts,
                            Tab::Alerts => Tab::Dashboard,
                        };
                    }
                    (_, KeyCode::Down) => match ui_state.tab {
                        Tab::Dashboard => ui_state.packet_scroll = ui_state.packet_scroll.saturating_add(1),
                        Tab::Connections => ui_state.conn_scroll = ui_state.conn_scroll.saturating_add(1),
                        Tab::Alerts => ui_state.alert_scroll = ui_state.alert_scroll.saturating_add(1),
                    },
                    (_, KeyCode::Up) => match ui_state.tab {
                        Tab::Dashboard => ui_state.packet_scroll = ui_state.packet_scroll.saturating_sub(1),
                        Tab::Connections => ui_state.conn_scroll = ui_state.conn_scroll.saturating_sub(1),
                        Tab::Alerts => ui_state.alert_scroll = ui_state.alert_scroll.saturating_sub(1),
                    },
                    _ => {}
                }
            }
        }

        if last_tick.elapsed() >= tick_rate {
            // Calculate rates
            {
                let s = state.read();
                let elapsed = ui_state.rate_ts.elapsed().as_secs_f64();
                if elapsed >= 1.0 {
                    let pps = ((s.total_packets - ui_state.last_pkt_count) as f64 / elapsed) as u64;
                    let bps = ((s.total_bytes - ui_state.last_byte_count) as f64 / elapsed) as u64;
                    drop(s);
                    let mut s = state.write();
                    s.packets_per_second = pps;
                    s.bytes_per_second = bps;
                    ui_state.last_pkt_count = s.total_packets;
                    ui_state.last_byte_count = s.total_bytes;
                    ui_state.rate_ts = Instant::now();
                }
            }
            last_tick = Instant::now();
        }
    }

    // Restore terminal
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen, DisableMouseCapture)?;
    terminal.show_cursor()?;

    Ok(())
}

fn render(f: &mut Frame, state: &Arc<RwLock<AppState>>, ui: &mut TuiState) {
    let s = state.read();

    // ── Outer layout ─────────────────────────────────────────
    let outer = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Header
            Constraint::Length(3), // Tabs
            Constraint::Min(0),    // Body
            Constraint::Length(1), // Status bar
        ])
        .split(f.size());

    // ── Header ───────────────────────────────────────────────
    let uptime = {
        let d = chrono::Local::now() - s.start_time;
        format!("{}:{:02}:{:02}", d.num_hours(), d.num_minutes() % 60, d.num_seconds() % 60)
    };

    let header = Paragraph::new(Line::from(vec![
        Span::styled(" ", Style::default()),
        Span::styled(
            "rust_packet_sniffer",
            Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
        ),
        Span::raw(format!(
            "  │  {} pkts  │  {} bytes  │  {}/s  │  {} flows  │  {}  │  {} alerts",
            s.total_packets,
            format_bytes(s.total_bytes),
            s.packets_per_second,
            s.connections.len(),
            uptime,
            s.alerts.len(),
        )),
    ]))
    .block(Block::default().borders(Borders::ALL).title(" Network Monitor "))
    .style(Style::default().fg(Color::Cyan));
    f.render_widget(header, outer[0]);

    // ── Tab bar ──────────────────────────────────────────────
    let tab_titles = vec!["  Dashboard  ", "  Connections  ", "  Alerts  "];
    let selected = match ui.tab {
        Tab::Dashboard => 0,
        Tab::Connections => 1,
        Tab::Alerts => 2,
    };
    let tabs = Tabs::new(tab_titles)
        .select(selected)
        .block(Block::default().borders(Borders::ALL))
        .highlight_style(
            Style::default()
                .fg(Color::Yellow)
                .add_modifier(Modifier::BOLD),
        )
        .style(Style::default().fg(Color::White));
    f.render_widget(tabs, outer[1]);

    // ── Body by tab ──────────────────────────────────────────
    match ui.tab {
        Tab::Dashboard => render_dashboard(f, outer[2], &s, ui),
        Tab::Connections => render_connections(f, outer[2], &s, ui),
        Tab::Alerts => render_alerts(f, outer[2], &s, ui),
    }

    // ── Status bar ───────────────────────────────────────────
    let status = Paragraph::new(Line::from(vec![
        Span::styled(" q", Style::default().fg(Color::Yellow)),
        Span::raw(":quit  "),
        Span::styled("Tab", Style::default().fg(Color::Yellow)),
        Span::raw(":switch  "),
        Span::styled("↑↓", Style::default().fg(Color::Yellow)),
        Span::raw(":scroll  "),
        Span::raw(format!(
            "  {:.1} KB/s in",
            s.bytes_per_second as f64 / 1024.0
        )),
    ]))
    .style(Style::default().fg(Color::DarkGray));
    f.render_widget(status, outer[3]);
}

fn render_dashboard(
    f: &mut Frame,
    area: ratatui::layout::Rect,
    s: &AppState,
    ui: &TuiState,
) {
    let cols = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(35), Constraint::Percentage(65)])
        .split(area);

    let left = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(55), Constraint::Percentage(45)])
        .split(cols[0]);

    // ── Protocol bar chart ───────────────────────────────────
    let mut proto_data: Vec<(String, u64)> = s.protocol_counts
        .iter()
        .map(|(k, v)| (k.clone(), *v))
        .collect();
    proto_data.sort_by(|a, b| b.1.cmp(&a.1));
    proto_data.truncate(6);
    let bar_data: Vec<(&str, u64)> = proto_data
        .iter()
        .map(|(k, v)| (k.as_str(), *v))
        .collect();

    let chart = BarChart::default()
        .block(Block::default().title(" Protocols ").borders(Borders::ALL))
        .data(&bar_data)
        .bar_width(6)
        .bar_gap(2)
        .bar_style(Style::default().fg(Color::Cyan))
        .value_style(Style::default().fg(Color::White).add_modifier(Modifier::BOLD));
    f.render_widget(chart, left[0]);

    // ── Top talkers ──────────────────────────────────────────
    let talker_items: Vec<ListItem> = s
        .top_talkers
        .iter()
        .enumerate()
        .map(|(i, (ip, bytes))| {
            let color = if i == 0 { Color::Red } else if i < 3 { Color::Yellow } else { Color::White };
            ListItem::new(Line::from(vec![
                Span::styled(format!("{:<16}", ip), Style::default().fg(color)),
                Span::raw(format!(" {}", format_bytes(*bytes))),
            ]))
        })
        .collect();

    let talkers = List::new(talker_items)
        .block(Block::default().title(" Top Talkers ").borders(Borders::ALL))
        .highlight_style(Style::default().add_modifier(Modifier::BOLD));
    f.render_widget(talkers, left[1]);

    // ── Recent packets log ───────────────────────────────────
    let pkts: Vec<ListItem> = s
        .recent_packets
        .iter()
        .rev()
        .skip(ui.packet_scroll)
        .take(area.height as usize)
        .map(|pkt| {
            let proto_color = match pkt.protocol.as_str() {
                "TCP" => Color::Cyan,
                "UDP" => Color::Green,
                p if p.starts_with("ICMP") => Color::Magenta,
                _ => Color::White,
            };
            let flag_color = if pkt.flags.syn && !pkt.flags.ack {
                Color::Red
            } else if pkt.flags.rst {
                Color::Yellow
            } else {
                Color::DarkGray
            };
            ListItem::new(Line::from(vec![
                Span::styled(
                    format!("{} ", pkt.timestamp),
                    Style::default().fg(Color::DarkGray),
                ),
                Span::styled(
                    format!("{:<6}", pkt.protocol),
                    Style::default().fg(proto_color).add_modifier(Modifier::BOLD),
                ),
                Span::raw(format!(" {:<15} → {:<15}", pkt.src_ip, pkt.dst_ip)),
                Span::styled(
                    format!(" {:<8}", pkt.flag_str()),
                    Style::default().fg(flag_color),
                ),
                Span::styled(
                    format!(" {}b", pkt.length),
                    Style::default().fg(Color::DarkGray),
                ),
            ]))
        })
        .collect();

    let log = List::new(pkts)
        .block(
            Block::default()
                .title(" Packet Log (↑↓ scroll) ")
                .borders(Borders::ALL),
        )
        .style(Style::default().fg(Color::White));
    f.render_widget(log, cols[1]);
}

fn render_connections(
    f: &mut Frame,
    area: ratatui::layout::Rect,
    s: &AppState,
    ui: &TuiState,
) {
    let header = Row::new(vec!["Protocol", "Source", "Destination", "State", "Pkts", "Bytes"])
        .style(Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD));

    let mut flows: Vec<_> = s.connections.values().collect();
    flows.sort_by(|a, b| b.byte_count.cmp(&a.byte_count));

    let rows: Vec<Row> = flows
        .iter()
        .skip(ui.conn_scroll)
        .take(area.height as usize - 3)
        .map(|f| {
            let state_color = match f.state {
                crate::types::ConnectionState::Established => Color::Green,
                crate::types::ConnectionState::SynSent => Color::Yellow,
                crate::types::ConnectionState::FinWait | crate::types::ConnectionState::Closed => Color::DarkGray,
                _ => Color::White,
            };
            Row::new(vec![
                Cell::from(f.protocol.clone()),
                Cell::from(format!("{}:{}", f.src, f.src_port)),
                Cell::from(format!("{}:{}", f.dst, f.dst_port)),
                Cell::from(f.state.to_string()).style(Style::default().fg(state_color)),
                Cell::from(f.packet_count.to_string()),
                Cell::from(format_bytes(f.byte_count)),
            ])
        })
        .collect();

    let table = Table::new(
        rows,
        [
            Constraint::Length(8),
            Constraint::Length(22),
            Constraint::Length(22),
            Constraint::Length(13),
            Constraint::Length(8),
            Constraint::Length(10),
        ],
    )
    .header(header)
    .block(
        Block::default()
            .title(format!(" Active Connections ({}) ", s.connections.len()))
            .borders(Borders::ALL),
    );
    f.render_widget(table, area);
}

fn render_alerts(
    f: &mut Frame,
    area: ratatui::layout::Rect,
    s: &AppState,
    ui: &TuiState,
) {
    let items: Vec<ListItem> = s
        .alerts
        .iter()
        .rev()
        .skip(ui.alert_scroll)
        .take(area.height as usize - 2)
        .map(|a| {
            let (color, icon) = match a.severity {
                AlertSeverity::Critical => (Color::Red, "🔴"),
                AlertSeverity::High => (Color::LightRed, "🟠"),
                AlertSeverity::Medium => (Color::Yellow, "🟡"),
                AlertSeverity::Low => (Color::Cyan, "🔵"),
            };
            ListItem::new(Line::from(vec![
                Span::raw(format!("{} ", icon)),
                Span::styled(
                    format!("[{}] ", a.timestamp.format("%H:%M:%S")),
                    Style::default().fg(Color::DarkGray),
                ),
                Span::styled(
                    format!("{:<8} ", a.severity),
                    Style::default().fg(color).add_modifier(Modifier::BOLD),
                ),
                Span::styled(
                    format!("{:<12} ", a.kind),
                    Style::default().fg(Color::White),
                ),
                Span::raw(a.message.clone()),
            ]))
        })
        .collect();

    let list = List::new(items)
        .block(
            Block::default()
                .title(format!(" Security Alerts ({}) ", s.alerts.len()))
                .borders(Borders::ALL),
        )
        .style(Style::default().fg(Color::White));
    f.render_widget(list, area);
}

fn format_bytes(b: u64) -> String {
    if b < 1024 {
        format!("{}B", b)
    } else if b < 1024 * 1024 {
        format!("{:.1}KB", b as f64 / 1024.0)
    } else if b < 1024 * 1024 * 1024 {
        format!("{:.1}MB", b as f64 / (1024.0 * 1024.0))
    } else {
        format!("{:.1}GB", b as f64 / (1024.0 * 1024.0 * 1024.0))
    }
}