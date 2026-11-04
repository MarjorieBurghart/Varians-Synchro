"""Le projet d'exemple livré (demo_local_ALTO/) est prêt pour le « Premier
essai » de l'aide : A y est déjà le témoin pivot, comme le serait le premier
témoin ajouté par la fiche du témoin."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'demo_local_ALTO' / 'exemple.vsynch'


def test_the_shipped_demo_has_a_as_its_pivot():
    assert json.loads(DEMO.read_text(encoding='utf-8'))['pivot_witness_id'] == 'A'


def test_the_demo_generator_makes_a_the_pivot(tmp_path):
    sys.path.insert(0, str(ROOT))
    try:
        import creer_demo
    finally:
        sys.path.remove(str(ROOT))
    output = creer_demo.main(tmp_path / 'demo')
    assert json.loads(output.read_text(encoding='utf-8'))['pivot_witness_id'] == 'A'
