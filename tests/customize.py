import pytest
import io

from app.middleware import db
from app.helpers import get_tts_safely
from app.database import (Touch_store, Display_store, Printer, Slides_c,
                          Vid, Media, Slides, Aliases)


@pytest.mark.usefixtures('c')
def test_welcome_customize(c):
    response = c.get('/customize', follow_redirects=True)
    page_content = response.data.decode('utf-8')

    assert response.status == '200 OK'
    assert 'Customization' in page_content


@pytest.mark.usefixtures('c')
def test_ticket_registered(c):
    with c.application.app_context():
        touch_screen_settings = Touch_store.get()
        touch_screen_settings.n = True
        db.session.commit()

    printer_value = 1
    response = c.post('/ticket',
                      data={'value': printer_value},
                      follow_redirects=True)

    assert response.status == '200 OK'
    assert Printer.get().value == printer_value
    assert Printer.get().active is False
    assert Touch_store.get().n is True


@pytest.mark.usefixtures('c')
def test_video(c):
    name = 'testing.mp4'
    ar = 1
    controls = 2
    mute = 2
    enable = 1
    video_id = 0

    with c.application.app_context():
        slides_settings = Slides_c.get()
        slides_settings.status = False
        video_settings = Vid.get()
        video_settings.enabled = True
        video = Media(True, name=name)

        db.session.add(video)
        db.session.commit()

        video_id = video.id

    response = c.post('/video', data={
        'video': video_id,
        'ar': ar,
        'enable': enable,
        'mute': mute,
        'controls': controls
    }, follow_redirects=True)

    assert response.status == '200 OK'
    assert Vid.get().enable == enable
    assert Vid.get().vname == name
    assert Vid.get().mute == mute
    assert Vid.get().ar == ar
    assert Vid.get().controls == controls
    assert Vid.get().vkey == video_id
    assert Media.get(video_id).used is True


@pytest.mark.usefixtures('c')
def test_slideshow(c):
    with c.application.app_context():
        slides_settings = Slides_c.get()
        slides_settings.status = True
        video_settings = Vid.get()
        video_settings.enabled = False

        db.session.commit()

    response = c.get('/slideshow', follow_redirects=True)
    page_content = response.data.decode('utf-8')

    assert response.status == '200 OK'
    for slide in Slides.query.all():
        assert f'{slide.id}. {slide.title}' in page_content


@pytest.mark.usefixtures('c')
def test_add_slide(c):
    with c.application.app_context():
        slides_settings = Slides_c.get()
        slides_settings.status = True
        video_settings = Vid.get()
        video_settings.enabled = False

        db.session.commit()

    properties = {'title': 'testing_title',
                  'hsize': '150%',
                  'hcolor': 'testing_hcolor',
                  'hfont': 'testing_hfont',
                  'hbg': 'testing_hbg',
                  'subti': 'teesting_subti',
                  'tsize': '150%',
                  'tcolor': 'testing_tcolor',
                  'tfont': 'testing_tfont',
                  'tbg': 'testing_tbg'}
    data = {'background': 0, **properties}
    response = c.post('/slide_a', data=data, follow_redirects=True)

    assert response.status == '200 OK'
    for key, value in properties.items():
        assert Slides.query.filter_by(**{key: value}).first() is not None


@pytest.mark.usefixtures('c')
def test_add_slide_image(c):
    background_id = 0

    with c.application.app_context():
        slides_settings = Slides_c.get()
        slides_settings.status = True
        video_settings = Vid.get()
        video_settings.enabled = False
        background = Media(img=True, name='testing.jpg')

        db.session.add(background)
        db.session.commit()

        background_id = background.id

    properties = {'title': 'testing_title',
                  'hsize': '150%',
                  'hcolor': 'testing_hcolor',
                  'hfont': 'testing_hfont',
                  'hbg': 'testing_hbg',
                  'subti': 'teesting_subti',
                  'tsize': '150%',
                  'tcolor': 'testing_tcolor',
                  'tfont': 'testing_tfont',
                  'tbg': 'testing_tbg'}
    data = {'background': background_id, **properties}
    response = c.post('/slide_a', data=data, follow_redirects=True)

    assert response.status == '200 OK'
    assert background_id != 0
    for key, value in properties.items():
        slide = Slides.query.filter_by(**{key: value}).first()

        assert slide is not None
        assert slide.ikey == background_id


@pytest.mark.usefixtures('c')
def test_update_slide(c):
    with c.application.app_context():
        slides_settings = Slides_c.get()
        slides_settings.status = True

        db.session.commit()

    rotation = '3000'
    navigation = 2
    effect = 'fade'
    status = 1
    response = c.post('/slide_c', data={
        'rotation': rotation,
        'navigation': navigation,
        'effect': effect,
        'status': status
    }, follow_redirects=True)

    assert response.status == '200 OK'
    assert Slides_c.get().rotation == rotation
    assert Slides_c.get().navigation == navigation
    assert Slides_c.get().effect == effect
    assert Slides_c.get().status == status


@pytest.mark.usefixtures('c')
def test_remove_slide(c):
    slide = None

    with c.application.app_context():
        slide = Slides.get()

    response = c.get(f'/slide_r/{slide.id}', follow_redirects=True)

    assert response.status == '200 OK'
    assert Slides.get(slide.id) is None


@pytest.mark.usefixtures('c')
def test_multimedia(c):
    name = 'test.jpg'
    content = b'testing image'
    data = {'mf': (io.BytesIO(content), name)}

    response = c.post('/multimedia/1',
                      data=data,
                      follow_redirects=True,
                      content_type='multipart/form-data')

    assert response.status == '200 OK'
    assert Media.query.filter_by(name=name).first() is not None


@pytest.mark.usefixtures('c')
def test_multimedia_wrong_extension(c):
    name = 'test.wrn'
    content = b'testing wrong'
    data = {'mf': (io.BytesIO(content), name)}

    response = c.post('/multimedia/1',
                      data=data,
                      follow_redirects=True,
                      content_type='multipart/form-data')

    assert response.status == '200 OK'
    assert Media.query.filter_by(name=name).first() is None


@pytest.mark.usefixtures('c')
def test_delete_multimedia(c):
    media_id = 0

    with c.application.app_context():
        media = Media(True, False, False, False, 'testing.mp3')

        db.session.add(media)
        db.session.commit()

        media_id = media.id

    response = c.get(f'/multi_del/{media_id}', follow_redirects=True)

    assert media_id != 0
    assert response.status == '200 OK'
    assert Media.get(media_id) is None


@pytest.mark.usefixtures('c')
def test_display_screen_customization(c):
    tts = get_tts_safely()
    properties = {
        'title': 'testing',
        'hsize': '500%',
        'hcolor': 'testing',
        'hbg': 'testing',
        'tsize': '200%',
        'tcolor': 'testing',
        'h2size': '150%',
        'h2color': 'testing',
        'ssize': '500%',
        'scolor': 'testing',
        'mduration': '2000',
        'hfont': 'testing',
        'tfont': 'testing',
        'h2font': 'testing',
        'sfont': 'testing',
        'rrate': '2000',
        'anr': 3,
        'anrt': 'each',
        'effect': 'bounce',
        'repeats': '2',
        'prefix': True,
        'always_show_ticket_number': True,
        'bgcolor': 'testing'
    }
    data = {f'check{s}': True for s in tts.keys()}
    data.update({'display': 1,
                 'background': 0,
                 'naudio': 0,
                 **properties})

    response = c.post('/displayscreen_c/1', data=data, follow_redirects=True)

    assert response.status == '200 OK'
    for key, value in properties.items():
        assert getattr(Display_store.get(), key, None) == value


@pytest.mark.usefixtures('c')
def test_touch_screen_customization(c):
    properties = {
        'title': 'testing',
        'hsize': '500%',
        'hcolor': 'testing',
        'hbg': 'testing',
        'mbg': 'testing',
        'tsize': '200%',
        'tcolor': 'btn-info',
        'msize': '300%',
        'mcolor': 'testing',
        'mduration': '1000',
        'hfont': 'testing',
        'tfont': 'testing',
        'mfont': 'testing',
        'message': 'testing',
    }

    data = {'touch': 2,
            'background': 0,
            'naudio': 0,
            **properties}

    response = c.post('/touchscreen_c/1', data=data, follow_redirects=True)

    assert response.status == '200 OK'
    for key, value in properties.items():
        assert getattr(Touch_store.get(), key, None) == value


@pytest.mark.usefixtures('c')
def test_aliases(c):
    data = {
        'office': 't_office',
        'task': 't_task',
        'ticket': 't_ticket',
        'name': 't_name',
        'number': 't_number',
    }

    response = c.post('/alias', data=data, follow_redirects=True)

    assert response.status == '200 OK'
    for key, value in data.items():
        assert getattr(Aliases.get(), key, None) == value
