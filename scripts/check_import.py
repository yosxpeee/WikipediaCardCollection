import sys
sys.path.insert(0, 'src')
try:
    import powerup
    import mockbattle
    import utils.ui
    print('IMPORT_OK')
except Exception as e:
    print('IMPORT_ERR', e)
    raise
