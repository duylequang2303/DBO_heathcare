"""P0 validation and whitelist checks for Cuong's backend demo scope."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.services import PRESET_PROFILES, get_food_map, build_profile
from app.api.schemas import ProfileIn
from src.models.food_selector import build_meal_pools

client = TestClient(app)

@pytest.mark.parametrize('seed', [-1, -123])
def test_negative_seed_rejected(seed):
    assert client.post('/api/menu/generate', json={'profile':PRESET_PROFILES['p1'],'seed':seed,'config':'smoke'}).status_code == 422
    assert client.post('/api/menu/swap', json={'profile':PRESET_PROFILES['p1'],'seed':seed,'food_ids':[],'slot':'lunch_0'}).status_code == 422

def test_allergy_single_letter_rejected():
    p = dict(PRESET_PROFILES['p1'],allergies=['a'])
    assert client.post('/api/targets',json=p).status_code == 422

def test_unknown_food_rejected():
    data={'profile':PRESET_PROFILES['p1'],'food_ids':['DOES_NOT_EXIST']*7,'slot':'lunch_0'}
    assert client.post('/api/menu/swap',json=data).status_code == 400

@pytest.mark.parametrize('portions', [['rác']*7, ['NaN']*7, [100]*6, [-100]*7])
def test_invalid_portions_rejected(portions):
    data={'profile':PRESET_PROFILES['p1'],'food_ids':['DOES_NOT_EXIST']*7,'slot':'lunch_0','old_portions_g':portions}
    assert client.post('/api/menu/swap',json=data).status_code == 422

def test_whitelist_three_profiles():
    foods=get_food_map()
    assert 150<=len(foods)<=300
    assert all(fid.startswith('VN_') and x['sodium_mg']>0 for fid,x in foods.items())
    for name,p in PRESET_PROFILES.items():
        profile=build_profile(ProfileIn(**p))
        pools=build_meal_pools(foods,profile.meal_counts,profile)
        assert all(len(candidates)>=20 for candidates in pools.values()),name

def test_hypertension_target():
    result=client.post('/api/targets',json=PRESET_PROFILES['p3'])
    assert result.status_code==200
    assert result.json()['targets']['sodium_mg']==1500
