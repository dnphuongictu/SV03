import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from vidroid_validator import validate
def item(**x):
    r={"id":"V1","utterance":"Goi cho me","language":"vi","intent":"call_contact","arguments":{"contact":"me"},"risk_level":"medium","split":"train"}; r.update(x); return r
class TestValidator(unittest.TestCase):
    def test_valid(self): self.assertEqual(validate([item()]),[])
    def test_required_argument(self): self.assertTrue(validate([item(arguments={})]))
    def test_split_leakage(self): self.assertTrue(validate([item(),item(id="V2",split="test")]))
if __name__=="__main__": unittest.main()
