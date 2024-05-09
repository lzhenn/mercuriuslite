#pip uninstall mercuriuslite 
#rm -rf build dist *egg-info
python setup.py sdist
pip install .
#cd toolbox 
#python gridsearch_ma_cross_schemer.py
#python test_inspect.py
