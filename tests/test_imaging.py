import json
import zipfile
from varians_synchro.core import new_project,create_witness,add_image_source,add_alto_source,save_project,load_project
from varians_synchro.imaging import parse_manifest,create_pages,bind_alto,mapped_alto_page,export_iiif_htr_zip,image_request_url

V2={'label':'Example','sequences':[{'canvases':[{'@id':'https://example.org/c1','label':'f. 14v','width':4000,'height':6000,'images':[{'resource':{'@id':'https://example.org/a.jpg','service':{'@id':'https://example.org/iiif/a'}}}]}]}]}
V3={'type':'Manifest','label':{'fr':['Exemple']},'items':[{'id':'https://example.org/c3','type':'Canvas','label':{'fr':['f. 16v']},'width':4000,'height':6000,'items':[{'type':'AnnotationPage','items':[{'motivation':'painting','body':{'id':'https://example.org/b.jpg','type':'Image','service':[{'id':'https://example.org/iiif/b','type':'ImageService3'}]}}]}]}]}

def test_manifest_v2_and_v3():
    a=parse_manifest(V2,'https://example.org/m');b=parse_manifest(V3)
    assert a['iiif_version']==2 and a['canvases'][0]['label']=='f. 14v'
    assert image_request_url({'image_kind':'iiif','canvas':a['canvases'][0]},2400)=='https://example.org/iiif/a/full/!2400,/0/default.jpg'
    assert b['iiif_version']==3 and b['canvases'][0]['label']=='f. 16v'
    assert image_request_url({'image_kind':'iiif','canvas':b['canvases'][0]},2400)=='https://example.org/iiif/b/full/2400,/0/default.jpg'

def test_pages_bindings_survive_refresh(tmp_path):
    p=new_project();w=create_witness(p,'A');src=add_image_source(w,'iiif','https://example.org/m');src['manifest']=parse_manifest(V2)
    create_pages(w)
    path=tmp_path/'alto.xml'
    path.write_text('<alto><Layout><Page WIDTH="100" HEIGHT="200"><PrintSpace><TextLine ID="l1" HPOS="1" VPOS="2" WIDTH="30" HEIGHT="10"/></PrintSpace></Page></Layout></alto>')
    alto=add_alto_source(w,path)
    bind_alto(w,w['pages'][0]['id'],alto['id'])
    assert mapped_alto_page(w,w['pages'][0])['line_count']==1
    create_pages(w)
    assert w['pages'][0]['alto_binding']['source_id']==alto['id']
    out=tmp_path/'project.vsynch';save_project(p,out)
    assert load_project(out)['witnesses'][0]['pages'][0]['alto_binding']['source_id']==alto['id']

def test_export_selected_images(monkeypatch,tmp_path):
    from varians_synchro import imaging
    w={'id':'A','pages':[{'id':'c1','label':'f. 14v','image_kind':'iiif','canvas':parse_manifest(V2)['canvases'][0]}]}
    monkeypatch.setattr(imaging,'image_bytes',lambda page,width:b'\xff\xd8' + b'image')
    dest=tmp_path/'export.zip'
    assert export_iiif_htr_zip(w,['c1'],dest)==1
    with zipfile.ZipFile(dest) as z:
        assert z.read('A_0001.jpg').startswith(b'\xff\xd8')
        assert json.loads(z.read('pages.json'))['pages'][0]['canvas_id']=='c1'

def test_do_not_export_bad_response(monkeypatch,tmp_path):
    from varians_synchro import imaging
    monkeypatch.setattr(imaging,'image_bytes',lambda page,width:b'<html>rate limit</html>')
    w={'id':'A','pages':[{'id':'c1','label':'p','image_kind':'iiif','canvas':parse_manifest(V2)['canvases'][0]}]}
    try:export_iiif_htr_zip(w,['c1'],tmp_path/'bad.zip')
    except ValueError:pass
    else:assert False
    assert not (tmp_path/'bad.zip').exists()

def test_htr_reimport(tmp_path):
    from varians_synchro.imaging import import_htr_results
    p=new_project();w=create_witness(p,'A');src=add_image_source(w,'iiif','https://example.org/m');src['manifest']=parse_manifest(V2)
    create_pages(w)
    mapping={'format':'varians-synchro-htr-export','witness':'A','pages':[{'file':'A_0001.jpg','canvas_id':w['pages'][0]['id']}]}
    mapping_path=tmp_path/'pages.json';mapping_path.write_text(json.dumps(mapping))
    alto=tmp_path/'A_0001.xml'
    alto.write_text('<alto><Layout><Page WIDTH="100" HEIGHT="200"><PrintSpace><TextLine ID="x"/></PrintSpace></Page></Layout></alto>')
    res=import_htr_results(w,mapping_path,tmp_path)
    assert len(res['imported'])==1
    assert mapped_alto_page(w,w['pages'][0])['line_count']==1
    res2=import_htr_results(w,mapping_path,tmp_path)
    assert len(res2['skipped'])==1
