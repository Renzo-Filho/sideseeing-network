import sys,unittest
from pathlib import Path
import pandas as pd,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from experiment_sp_allocations import choose_weights
class AllocationTests(unittest.TestCase):
 def data(self):return pd.DataFrame({'cep':['a','a','b','b','c'],'business_area':[70.,30.,0.,0.,0.],'establishment_addresses':[1.,3.,0.,0.,0.],'residential_area':[20.,80.,3.,1.,0.],'mixed_area':[0.,0.,0.,0.,0.]})
 def test_contrasting_geographic_rules(self):
  s=self.data();a,_=choose_weights(s,'area_first');b,_=choose_weights(s,'address_first');h,_=choose_weights(s,'hybrid')
  np.testing.assert_allclose(a[:2],[.7,.3]);np.testing.assert_allclose(b[:2],[.25,.75]);np.testing.assert_allclose(h[:2],[.475,.525])
 def test_fallback_and_no_support_not_fabricated(self):
  s=self.data();w,method=choose_weights(s,'area_first');np.testing.assert_allclose(w[2:4],[.75,.25]);self.assertEqual(method[2],'residential_fallback');self.assertEqual(w.iloc[4],0)
 def test_mass_and_scale_invariance(self):
  s=self.data();a,_=choose_weights(s,'area_first');s.business_area*=100;b,_=choose_weights(s,'area_first');np.testing.assert_allclose(a,b);self.assertAlmostEqual(float((a[:2]*1000).sum()),1000)
if __name__=='__main__':unittest.main()
