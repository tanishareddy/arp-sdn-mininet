from pox.core import core
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class ARPHandler(object):
    def __init__(self, connection):
        self.connection = connection
        # Table to store IP -> MAC mappings
        self.arp_table = {}
        connection.addListeners(self)
        log.info("ARPHandler initialized on %s" % connection)

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        # Learn the source MAC and IP from every packet
        src_mac = packet.src
        src_ip = None

        # Handle ARP packets
        if packet.type == ethernet.ARP_TYPE:
            arp_packet = packet.payload

            # Learn the sender's IP -> MAC mapping
            src_ip = arp_packet.protosrc
            self.arp_table[src_ip] = src_mac
            log.info("Learned: %s is at %s" % (src_ip, src_mac))

            # Handle ARP Request
            if arp_packet.opcode == arp.REQUEST:
                target_ip = arp_packet.protodst
                log.info("ARP Request: Who has %s? Tell %s" % (target_ip, src_ip))

                # Check if we know the target IP
                if target_ip in self.arp_table:
                    target_mac = self.arp_table[target_ip]
                    log.info("ARP Reply: %s is at %s (from controller)" % (target_ip, target_mac))

                    # Build ARP reply packet
                    arp_reply = arp()
                    arp_reply.opcode = arp.REPLY
                    arp_reply.hwsrc = target_mac
                    arp_reply.hwdst = src_mac
                    arp_reply.protosrc = target_ip
                    arp_reply.protodst = src_ip

                    # Wrap in ethernet frame
                    eth_reply = ethernet()
                    eth_reply.type = ethernet.ARP_TYPE
                    eth_reply.src = target_mac
                    eth_reply.dst = src_mac
                    eth_reply.payload = arp_reply

                    # Send reply back out the same port
                    msg = of.ofp_packet_out()
                    msg.data = eth_reply.pack()
                    msg.actions.append(of.ofp_action_output(port=event.port))
                    self.connection.send(msg)
                    log.info("Sent ARP reply to %s" % src_ip)

                else:
                    # Flood the ARP request if we don't know the target
                    log.info("Target %s unknown, flooding ARP request" % target_ip)
                    msg = of.ofp_packet_out()
                    msg.data = event.ofp
                    msg.in_port = event.port
                    msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
                    self.connection.send(msg)

            # Handle ARP Reply
            elif arp_packet.opcode == arp.REPLY:
                log.info("ARP Reply received: %s is at %s" % (arp_packet.protosrc, arp_packet.hwsrc))
                # Forward the reply to the correct host
                msg = of.ofp_packet_out()
                msg.data = event.ofp
                msg.in_port = event.port
                msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
                self.connection.send(msg)

        else:
            # For non-ARP packets, install a flow rule or flood
            msg = of.ofp_packet_out()
            msg.data = event.ofp
            msg.in_port = event.port
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            self.connection.send(msg)


class ARPHandlerLauncher(object):
    def __init__(self):
        self.arp_table = {}
        core.openflow.addListeners(self)
        log.info("ARP Handler Launch - Waiting for switches...")

    def _handle_ConnectionUp(self, event):
        log.info("Switch connected: %s" % event.connection)
        ARPHandler(event.connection)


def launch():
    core.registerNew(ARPHandlerLauncher)
    log.info("ARP Handler module launched!")      
