import numpy as np
import acsys.dpm
import acsys.scaling

async def update_ramp_list(con, device_list, value_list,settings_role):
    settings_l = [None]*len(device_list)
    async with acsys.dpm.DPMContext(con) as dpm:
        await dpm.enable_settings(role=settings_role)
        for i, value in enumerate(device_list):
            await dpm.add_entry(i, value+'.RAW@i')
        await dpm.start()
        async for reply in dpm.replies():
            #if reply.isReadingFor(0):
            raw = await acsys.scaling.convert_data(con, device_list[reply.tag]+'.RAW@i', value_list[reply.tag])
            settings_l[reply.tag]= raw + reply.data[-2:]
            if settings_l.count(None)==0:
                break
            #if reply.isStatusFor(0):
            #    raise reply.status
        setpairs = list(enumerate(settings_l))
        print(setpairs)
        await dpm.apply_settings(setpairs)
        print('settings applied')
        async for reply in dpm.replies(tmo=0.25):
            print(reply)
            break
    return None

async def read_settings(con,drf_list):
    settings_l = [None]*len(drf_list)
    async with acsys.dpm.DPMContext(con) as dpm:
        for i in range(len(drf_list)):
            await dpm.add_entry(i, drf_list[i]+'@i')
        await dpm.start()
        async for reply in dpm:
            settings_l[reply.tag]=reply.data
            if settings_l.count(None) ==0:
                break
    return settings_l

class qt60:
    def __init__(self):
        self.base_qx = 25.4561
        self.base_qy = 24.3926
        self.trombone_coeffs = np.array([
    [-127.4009, 1557.4331, 126.8515,-1616.3387, -57.7456, 1652.6903, 31.9635, -1709.2477,-56.3398],
    [32.0604, 62.5516, -35.9780, -57.4829, 34.4453, 26.3437, -38.6868, -30.1116, 34.9921],
    [6331.2382, -1473.0529, -4507.5945, 1874.9018, 3429.3563, -1761.9906, -1801.8841, 1883.5916, 344.88945],
    [-161.2757, -25.7280, 150.3993, 11.1356, -192.9018, -18.2752, 165.4002, 6.5259, -215.4235],
    [2.7781, 15.0304, 3.0629, 15.3942, 2.7869, 15.0919, 3.0956, 15.6488, 2.8307],
    [-16.3347, -2.9164, -14.0461, -2.8762, -16.4531, -2.9237, -13.5865, -2.8196, -17.1834]])

    def get_qt60_trombone_settings(self, delta_nux, delta_nuy):
        b = np.array([6.6187e-7, 1.3967e-7, 1.2060e-5,3.8758e-8,delta_nux,delta_nuy])
        kcoeff = np.linalg.lstsq(self.trombone_coeffs, b,rcond=0)
        return kcoeff[0]

    def get_tunes_from_currents(self,currents):
        qt_length=0.3048
        qt_integrated_strength = 0.00297
        k = currents*qt_length*qt_integrated_strength
        b = np.dot(self.trombone_coeffs,k)
        xtune = b[-2] + self.base_qx
        ytune = b[-1] + self.base_qy
        return xtune, ytune

    def get_qt60_trombone_currents(self, xtune, ytune):
        delta_nux = xtune - self.base_qx
        delta_nuy = ytune - self.base_qy 
        qt_length=0.3048
        qt_integrated_strength = 0.00297
        return self.get_qt60_trombone_settings(delta_nux, delta_nuy)/qt_length/qt_integrated_strength

    def build_device_list(self,timeslot):
        index=timeslot
        qt_list = ['R:QT60'+str(i)+'T' for i in range(1,10)]
        drf_list=[]
        for qt in qt_list:
            drf = f'{qt}.SETTING[{index}]'
            drf_list.append(drf)
        return drf_list

    def set_tune(self, xtune_list, ytune_list, timeslot_list):
        for i in range(len(timeslot_list)):
            currents=self.get_qt60_trombone_currents(xtune_list[i], ytune_list[i]).tolist()
            drf_list = self.build_device_list(timeslot_list[i]) 
            acsys.run_client(update_ramp_list,device_list=drf_list, value_list=currents,settings_role='rr_tune_control')
            print(drf_list,currents)
        
    def get_currents(self,timeslot):
        drf_list = self.build_device_list(timeslot) 
        currents= acsys.run_client(read_settings, drf_list=drf_list) 
        return np.array(currents)

    def get_tune(self, timeslot):
        currents=self.get_currents(timeslot)
        tunes = self.get_tunes_from_currents(currents)
        return tunes[0], tunes[1]




    
