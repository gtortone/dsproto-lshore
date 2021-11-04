#!/usr/bin/env python3

import sys
import midas
import argparse
import midas.frontend
import midas.event
from lakeshore import Model336

### params
ls336_ipaddr = '172.16.12.218'
###

class Lakeshore336(midas.frontend.EquipmentBase):

    def __init__(self, client, ipaddr):
        equip_name = "Lakeshore-336"

        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_PERIODIC
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 300
        default_common.period_ms = 5000
        default_common.read_when = midas.RO_ALWAYS
        default_common.log_history = 1

        self.inputs = ['A', 'B', 'C', 'D']
        self.gettemp_str = "KRDG? %s"
        self.getflag_str = "RDGST? %s"

        self.ipaddr = ipaddr
        try:
            self.ls336 = Model336(ip_address=ipaddr)
        except Exception as e:
            print("E: fail to connect on IP: %s" % ipaddr)
            print(e)
            sys.exit(-1)

        midas.frontend.EquipmentBase.__init__(self, client, equip_name, default_common)

        self.set_status("Initialized")

    def readout_func(self):
        event = midas.event.Event()

        # temperature values list
        t_list = []
        # input flags
        f_list = []

        for probe in self.inputs:

            print(probe)
            try:
                readval = self.ls336.query(self.gettemp_str % str(probe))
            except InstrumentException as e:
                self.client.msg("Lakeshore frontend InstrumentException - renew TCP connection", True)
                self.ls336 = Model336(ip_address=self.ipaddr)
                return
            except Exception as e:
                #t_list.append(9999)
                return
            else:
                try:
                    freadval = float(readval)
                    print(freadval)
                except:
                    print("E: value %s cannot be converted to float" % readval)
                    return
                    #continue
                else:
                    t_list.append(float(readval))

            try:
                readval = self.ls336.query(self.getflag_str % str(probe))
                print(readval)
            except InstrumentException as e:
                self.client.msg("Lakeshore frontend InstrumentException - renew TCP connection", True)
                self.ls336 = Model336(ip_address=self.ipaddr)
                return
            except Exception as e:
                #f_list.append(9999)
                return
            else:
                try:
                    f_list.append(int(readval))
                except Exception as e:
                    #continue
                    return

        print("===")

        event.create_bank("TEMP", midas.TID_FLOAT, t_list)
        event.create_bank("FLAG", midas.TID_INT, f_list)

        return event

class MyFrontend(midas.frontend.FrontendBase):
    def __init__(self):
        midas.frontend.FrontendBase.__init__(self, "felakeshore")
        self.add_equipment(Lakeshore336(self.client, ls336_ipaddr))

    def begin_of_run(self, run_number):
        self.set_all_equipment_status("Lakeshore FE running", "greenLight")
        self.client.msg("Frontend has seen start of run number %d" % run_number)
        return midas.status_codes["SUCCESS"]

    def end_of_run(self, run_number):
        self.set_all_equipment_status("Lakeshore FE finished", "greenLight")
        self.client.msg("Frontend has seen end of run number %d" % run_number)
        return midas.status_codes["SUCCESS"]

if __name__ == "__main__":
    my_fe = MyFrontend()
    my_fe.run()
