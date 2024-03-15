from streamlit.testing.v1 import AppTest


def test_main():
    # see: https://docs.streamlit.io/library/advanced-features/app-testing
    at = AppTest.from_file("app.py")
    # at.run()
