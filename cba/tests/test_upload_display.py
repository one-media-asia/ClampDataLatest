import os
import io
import sys#test

# Ensure project root is on sys.path so `import app` works when pytest runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, ClampData


def test_upload_and_display(tmp_path):
    # ensure uploads folder exists under the real app root (templates are loaded from there)
    orig_root = app.root_path
    upload_dir = os.path.join(orig_root, 'static', 'images', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    # use in-memory sqlite for tests
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        # fresh schema
        db.drop_all()
        db.create_all()

        client = app.test_client()

        data = {
            'location': 'Test Location',
            'registration': 'TEST123',
            'clamp_date': '2025-11-27',
            'time_in': '12:00',
            'time_called': '12:05',
            'time_released': '',
            'offense': 'Blocking driveway',
            'payment_status': 'Processing',
            'amount_paid': '0.00',
            'car_type': 'Hatchback',
            'color': 'Red',
            'clamp_ref': 'REF-UNIT-001'
        }

        file_tuple = (io.BytesIO(b'test-image-bytes'), 'test.jpg')

        # set a dummy logged-in user id to pass the app's require_login check
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        resp = client.post('/add-clamp', data={**data, 'image': file_tuple}, content_type='multipart/form-data', follow_redirects=True)
        # should redirect back to index on success
        assert resp.status_code == 200
        resp_text = resp.get_data(as_text=True)

        # ensure record created
        clamp = ClampData.query.first()
        if clamp is None:
            # show response body to help diagnose server-side error
            raise AssertionError(f'No record created. Response body:\n{resp_text}')
        assert clamp.image_filename, 'image_filename should be set on the record'

        # file should exist under the temporary static folder
        image_path = os.path.join(app.root_path, 'static', clamp.image_filename)
        assert os.path.exists(image_path), f'Uploaded image not found at {image_path}'

        # index/listing should include the image path
        list_resp = client.get('/clamp_list')
        assert list_resp.status_code == 200
        body = list_resp.get_data(as_text=True)
        assert clamp.image_filename in body or 'test.jpg' in body

    # cleanup created test file(s) if any
    # (we leave the folder itself in place)
