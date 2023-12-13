#pip uninstall mercuriuslite 
#rm -rf build dist *egg-info
python setup.py sdist
pip install .
cd test_case
python test_schemer.py
#cd toolbox 
#python gridsearch_ma_cross_schemer.py
#python test_inspect.py
cd ..
