import tempfile
from pathlib import Path

from varians_synchro.core import (new_project, create_witness, add_alto_source,
                                 check_alto_files)

ALTO = '''<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout>
<Page ID="pg1" WIDTH="500" HEIGHT="500"><PrintSpace>
<TextLine ID="l1" HPOS="1" VPOS="2" WIDTH="40" HEIGHT="9">
<String CONTENT="Misericordia"/></TextLine></PrintSpace></Page></Layout></alto>'''


def test_external_alto_change_detected_without_mutating_project():
    with tempfile.TemporaryDirectory() as dirname:
        path = Path(dirname)/'one.xml'
        path.write_text(ALTO, encoding='utf-8')
        p=new_project();w=create_witness(p,'A')
        src=add_alto_source(w,path)
        assert src['source_sha256']
        assert check_alto_files(p) == []
        path.write_text(ALTO.replace('Misericordia','Caritas'),encoding='utf-8')
        assert 'modifié' in '\n'.join(check_alto_files(p))
        assert src['pages'][0]['lines'][0]['text']=='Misericordia'
        path.unlink()
        assert 'introuvable' in '\n'.join(check_alto_files(p))
