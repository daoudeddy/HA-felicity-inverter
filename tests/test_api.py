from __future__ import annotations

import importlib.util
import unittest

HOMEASSISTANT_AVAILABLE = importlib.util.find_spec("homeassistant") is not None

if HOMEASSISTANT_AVAILABLE:
    from custom_components.felicity_inverter.api import merge_json_objects, split_json_objects
else:  # pragma: no cover - environment dependent
    merge_json_objects = split_json_objects = None

SET_INFO = (
    '{"CommVer":1,"DevSN":"020906004825471655","ttlPack":2,"index":1,"Type":80,'
    '"BVolA":2068,"BVolBL":-4108,"InVolA":2050,"BVolBH":65525,"BVolBV":0,'
    '"InCurA":2046,"OpCurA":2056,"ShCurA":2056,"USIDTy":0,"bCOffV":480,'
    '"BVolOS":0,"BVoltL":0,"bCVCV":576,"bFCVo":576,"MHiLos":0,"MLoLOs":0,'
    '"MFqHLo":0,"MFqLLo":0,"outVol":2300,"opFreq":0,"oSPri":2,"appMo":1,'
    '"cSPri":3,"batTy":3,"MCCur":60,"MACCurr":10,"buzEn":1,"oLRst":0,'
    '"oTRst":0,"bFEn":0,"oL2Byp":0,"EStore":1,"Fp2Gd":0,"bB2CV":460,'
    '"outMod":0,"bB2DcV":540,"SCCOK":0,"mpptBA":0,"LWaitS":0,"O2StTm":0,'
    '"O2EdTm":5947,"O2OpTm":65535,"O2LVol":540,"O2LSOC":600,"CEnLog":0,'
    '"FctRst":60012,"rsPVol":2048,"rsPCur":2048,"rsPTyp":0,"GPowMx":500,'
    '"GChgEn":1,"oGdOP2":1}'
    '{"CommVer":1,"DevSN":"020906004825471655","ttlPack":2,"index":2,"Type":80,'
    '"BSOCUN":25,"BBkUt":35,"BBkBat":40,"hisDEn":1,"batEqE":0,"batEqV":584,'
    '"batEqT":60,"btEqTO":120,"btEqTI":30,"btEqAI":0,"ROffEn":0,"FltClr":0}'
)

REAL_INFO = (
    '{"CommVer":1,"wifiSN":"I020906004825471655","date":"20260310084150",'
    '"DevSN":"020906004825471655","Type":80,"SubType":1035,"workM":3,"bCStat":1,'
    '"pFlow":62689,"pFlowE1":0,"warn":0,"fault":0,"lPerc":30,"busVp":4315,'
    '"busVn":0,"bmsNum":1,"setWifi":2,"BatTem":15,"BMSFlE":1,"cSPri":3,'
    '"MACCurr":10,"ACin":[[2224,null,null],[0,null,null],[4941,null,null],[0,0],[0,null,null]],'
    '"ACout":[[2304,null,null],[9,null,null],[4941,null,null],[180,207,0],[180,null,null]],'
    '"PV":[[1823,0,0],[64,0,0],[1176,0,0],[0]],"Temp":[[380,300,340]],'
    '"Batt":[[55970],[140],[783,0]],"Batsoc":[[9700,0,0]],"BMSFlg":1,"BFlgAll":3,'
    '"Energy":[[0,1536,1536,1536,1536],[0,2485,863,2485,2485],[null],[null],[null],[null],'
    '[null],[null],[0,0,0,0,0],[0,0,0,0,0]],"GEN":[[0,null,null],[0,null,null],[0,null,null],[0,0],[0,null,null]],'
    '"SmartL":[[0,null,null],[0,null,null],[0,null,null],[0,0],[0,null,null]],"SmartS":0,"SPStus":0}'
    '{"CommVer":1,"wifiSN":"I020906004825471655","version":"2.13","DevSN":"072604810025520550",'
    '"InvSN":"020906004825471655","date":"20260310084150","Type":112,"ModAddr":1,'
    '"BBfault":0,"BBwarn":0,"Templist":[[190,180],[1,0],[null],[null]],"BattList":[[55870,null],[150,null]],'
    '"BatsocList":[[9700,1000,100000]],"BMaxMin":[[3520,3490],[0,3]],"BMSpara":[[1,2]],'
    '"Bstate":9152,"BLVolCu":[[576,480],[150,1000]],"BatcelList":[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],'
    '"BtemList":[[0,0,0,0,0,0,0,0]]}'
)


class ApiParsingTests(unittest.TestCase):
    @unittest.skipUnless(HOMEASSISTANT_AVAILABLE, "homeassistant not installed")
    def test_split_json_objects_parses_multiple_payloads(self) -> None:
        objects = split_json_objects(SET_INFO)

        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0]["index"], 1)
        self.assertEqual(objects[1]["index"], 2)

    @unittest.skipUnless(HOMEASSISTANT_AVAILABLE, "homeassistant not installed")
    def test_split_json_objects_parses_real_and_bms_packets(self) -> None:
        objects = split_json_objects(REAL_INFO)

        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0]["Type"], 80)
        self.assertEqual(objects[1]["Type"], 112)

    @unittest.skipUnless(HOMEASSISTANT_AVAILABLE, "homeassistant not installed")
    def test_merge_json_objects_uses_last_write_wins(self) -> None:
        merged = merge_json_objects([
            {"ttlPack": 2, "index": 1, "CommVer": 1},
            {"index": 2, "FltClr": 0},
        ])

        self.assertEqual(
            merged,
            {
                "ttlPack": 2,
                "index": 2,
                "CommVer": 1,
                "FltClr": 0,
            },
        )
