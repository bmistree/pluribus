from ryu.controller.controller import Datapath, _deactivate
from ryu.ofproto import ofproto_common
from ryu.ofproto import ofproto_parser
from ryu.ofproto import ofproto_protocol
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import nx_match
from ryu.controller import ofp_event

class PrincipalDatapath(Datapath):
    
    # Low level socket handling layer
    @_deactivate
    def _recv_loop(self):
        buf = bytearray()
        required_len = ofproto_common.OFP_HEADER_SIZE

        count = 0
        while self.is_active:
            ret = self.socket.recv(required_len)
            if len(ret) == 0:
                self.is_active = False
                break
            buf += ret
            while len(buf) >= required_len:
                (version, msg_type, msg_len, xid) = ofproto_parser.header(buf)
                required_len = msg_len
                if len(buf) < required_len:
                    break

                msg = ofproto_parser.msg(self,
                                         version, msg_type, msg_len, xid, buf)
                # LOG.debug('queue msg %s cls %s', msg, msg.__class__)
                if msg:
                    ev = ofp_event.ofp_msg_to_ev(msg)
                    print '\n\nGot an event to process\n\n'
                    
                    # self.ofp_brick.send_event_to_observers(ev, self.state)

                    # dispatchers = lambda x: x.callers[ev.__class__].dispatchers
                    # handlers = [handler for handler in
                    #             self.ofp_brick.get_handlers(ev) if
                    #             self.state in dispatchers(handler)]
                    # for handler in handlers:
                    #     handler(ev)

                buf = buf[required_len:]
                required_len = ofproto_common.OFP_HEADER_SIZE

                # We need to schedule other greenlets. Otherwise, ryu
                # can't accept new switches or handle the existing
                # switches. The limit is arbitrary. We need the better
                # approach in the future.
                count += 1
                if count > 2048:
                    count = 0
                    hub.sleep(0)

