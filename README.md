# arp-sdn-mininet
SDN-based ARP request and reply handling using Mininet and POX controller

# ARP Handling in SDN Networks

## Problem Statement
Implement ARP request and reply handling using the SDN controller (POX) with Mininet.
The controller intercepts ARP packets, generates ARP responses, enables host discovery,
and validates communication between hosts.

## What This Project Does
In traditional networks, ARP requests are broadcast to every host causing flooding and
security issues. This project implements an ARP Proxy using a POX SDN controller that:
- Intercepts all ARP requests before they flood the network
- Learns IP to MAC mappings of all hosts automatically
- Replies to ARP requests directly from its table (no flooding)
- Falls back to flooding only when a host is unknown (first time)

## Network Topology
- H1 (10.0.0.1) connected to Switch S1
- H2 (10.0.0.2) connected to Switch S1
- S1 connected to POX Controller

## Requirements
- Ubuntu 20.04/22.04/24.04 (or WSL2 on Windows)
- Mininet
- POX Controller
- Python 3.x
- Open vSwitch

## Setup and Installation

### 1. Install Mininet
```bash
sudo apt update
sudo apt install mininet -y
```

### 2. Install POX Controller
```bash
cd ~
git clone https://github.com/noxrepo/pox
```

### 3. Clone This Repository
```bash
git clone https://github.com/tanishareddy/arp-sdn-mininet.git
```

### 4. Copy ARP Handler to POX
```bash
cp ~/arp-sdn-mininet/arp_handler.py ~/pox/ext/
```

## How to Run

### Terminal 1 - Start POX Controller
```bash
cd ~/pox
python3 pox.py log.level --DEBUG arp_handler
```

### Terminal 2 - Start Mininet
```bash
sudo mn --controller=remote,ip=127.0.0.1,port=6633
```

## Test Scenarios

### Scenario 1 - Unknown Host Discovery (Flooding)
When the controller sees a host for the first time, it floods once to discover it.
```bash
mininet> pingall
```
Expected output in controller:
Learned: 10.0.0.1 is at xx:xx:xx:xx
ARP Request: Who has 10.0.0.2? Tell 10.0.0.1
Target 10.0.0.2 unknown, flooding ARP request
Learned: 10.0.0.2 is at xx:xx:xx:xx

### Scenario 2 - Known Host Proxy ARP (No Flooding)
Once the controller knows both hosts, it replies directly without flooding.
```bash
mininet> h1 ping -c 5 h2
mininet> h2 ping -c 5 h1
```
Expected output in controller:
ARP Reply: 10.0.0.1 is at xx:xx:xx:xx (from controller)
Sent ARP reply to 10.0.0.2

## Expected Output

### pingall
*** Results: 0% dropped (2/2 received)

### h1 ping -c 5 h2
5 packets transmitted, 5 received, 0% packet loss
rtt min/avg/max/mdev = 1.869/3.096/5.637/1.428 ms

### iperf Throughput Test
```bash
mininet> h1 iperf -s &
mininet> h2 iperf -c 10.0.0.1 -t 5
```
Bandwidth: 8.59 Mbits/sec

### ARP Table Verification
```bash
mininet> h1 arp -n
mininet> h2 arp -n
```
H1 knows: 10.0.0.2 is at 56:1f:e1:64:b2:f1
H2 knows: 10.0.0.1 is at 3a:4a:22:16:be:9c

## Performance Metrics
| Metric | Result |
|--------|--------|
| Packet Loss | 0% |
| Average Latency | ~3ms |
| Throughput | 8.59 Mbits/sec |

## Proof of Execution

### Screenshot 1 - POX Controller ARP Logs
Shows host discovery, ARP interception, and proxy ARP replies from the controller.
![POX ARP Logs](screenshots/pox_arp_logs.png)

### Screenshot 2 - pingall Results
Shows 0% packet loss confirming all hosts can communicate.
![pingall Results](screenshots/pingall.png)

### Screenshot 3 - ping Results
Shows latency measurements between H1 and H2.
![Ping Results](screenshots/ping_results.png)

### Screenshot 4 - iperf Throughput
Shows bandwidth measurement of 8.59 Mbits/sec between hosts.
![iperf Results](screenshots/iperf_results.png)

### Screenshot 5 - ARP Table
Shows H1 and H2 have learned each others MAC addresses through the controller.
![ARP Table](screenshots/arp_table.png)

## How It Works
1. Host H1 sends an ARP Request - Who has 10.0.0.2?
2. Switch forwards it to POX controller as a packet_in event
3. Controller checks its ARP table
4. If unknown - floods once, learns the MAC, updates table
5. If known - generates ARP Reply itself (Proxy ARP)
6. Hosts communicate directly after MAC discovery



