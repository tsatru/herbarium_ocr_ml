import pandas as pd
import psycopg2
from sklearn import svm
import numpy as np

def exp_range(start, end, e):  #se define la función exp_range que recibe: start, end y 'e'
    retval = []  #crea una lista llamada retval
    while start < end:   #mientras start sea menor a end 
        retval.append(start) #agrega un elemento a start
        start *= e   #multiplica start * e y asigna el resultado a "e"
    return retval #devuelve la lista retval hasta que la condición se vuelve falsa 



folds = 4         # el grupo de datos se divide en 4 subgrupos
perc_data = 0.3  # se define el porcentaje de la muestra de los datos
cache_size = 500  # SVM kernel cache

user = "root"
passwd = "tAn1a.ccud"

db = MySQLdb.connect(host="localhost",
                     user=user,
                     passwd=passwd,
                     db="mlproject")

cur_mysql = db.cursor()

sql =  """  
       SELECT id, occid, LENGTH(TRIM(text)) as "text_len", label, scaled_area_x0, scaled_area_y0, scaled_line_x0, scaled_line_y0, scaled_word_x0, scaled_word_y0, text \
       FROM input \
       WHERE scaled_area_x0 >= 0 AND scaled_area_x0 <= 1 \
       AND scaled_area_y0 >= 0 AND scaled_area_y0 <= 1 \
       AND scaled_line_x0 >= 0 AND scaled_line_x0 <= 1 \
       AND scaled_line_y0 >= 0 AND scaled_line_y0 <= 1 \
       AND scaled_word_x0 >= 0 AND scaled_word_x0 <= 1 \
       AND scaled_word_y0 >= 0 AND scaled_word_y0 <= 1;
       """  
      
my_engine='mysql+mysqldb://root:tAn1a.ccud@localhost/mlproject?charset=utf8mb4'        
#se almacena el resultado de la query como dataframe       
df = pd.read_sql_query(sql, my_engine)



# Optionally remove all locality labeled items
#df = df[(df["label"] != "locality")]
#print df.describe()
#exit()


# Randomly select data (very small slice to begin with for performance reasons)
df['is_train'] = np.random.uniform(0, 1, len(df)) <= perc_data 
#dentro de un array genera una muestra aleatoria que se encuentran dentro del rango 0-1
#siempre y cuando sea menor o igual que el perc_data(0.01)
# Yes, some of our test may show up as train too using this random method, below
# full set is better but prediction is longer
#df['is_test'] = np.random.uniform(0, 1, len(df)) <= perc_data
df['is_test'] = df['is_train'] == False #crea tabla de prueba, siempre y cuando los valores del df de entrenamiento sean distintos al df de prueba
train_df = df[(df['is_train'])]  #define el df de entrenamiento
test_df = df[(df['is_test'])] #define el df de prueba
print "Selected", len(train_df), "training samples and", len(test_df), "testing samples."  #imprime el tamaño de cada una de los df

#se crea el diccionario feature_sets  con tres listas word, line y area
feature_sets = {
                   "word": ['scaled_word_x0', 'scaled_word_y0'],
                   "line": ['scaled_word_x0', 'scaled_word_y0', 'scaled_line_x0', 'scaled_line_y0'],
                   "area": ['scaled_word_x0', 'scaled_word_y0', 'scaled_line_x0', 'scaled_line_y0', 'scaled_area_x0', 'scaled_area_y0']
               }

model_results = []   #se crea la lista model_results
best_score = 0  #se define best score
for feat_name, features in feature_sets.iteritems():     #itera dentro del diccionario (key, value)

    #  convierte arreglos en inputs y etiquetas separadas
    train_features = np.array(train_df[features]) #crea un arreglo a partir del df de entrenamiento con sus features
    train_labels = np.array(train_df['label'], dtype=str) # see https://github.com/scikit-learn/scikit-learn/issues/2374, crea un arreglo con etiquetas del df de entrenamiento
    test_features = np.array(test_df[features])
    test_labels = np.array(test_df['label'], dtype=str)

    # Tune C and gamma through cross validation
    classifier = svm.SVC(cache_size=cache_size)  #se define el clasificador, es éste caso SVC
    cv = cross_validation.KFold(len(train_features), n_folds = folds)  #divide df train en 4 sets
    # Parameter ranges ref: page 5
    # Reverse to try to get large C's up front to mix better with faster smaller C's, improve runtime
    param_grid = {"C": exp_range(pow(2, -5), pow(2, 15), 2)[::-1],   #calcula c y gamma dentro de un diccionario
                  "gamma": exp_range(pow(2, -15), pow(2, 3), 2)[::-1]}  
    # Small testing range
    #param_grid = {"C": [1, 10, 100], "gamma": [0, 0.001, 0.1]}
    #gs = grid_search.GridSearchCV(classifier, param_grid=param_grid, cv=cv, verbose=1, n_jobs=-1) 
    gs = grid_search.GridSearchCV(classifier, param_grid=param_grid, cv=cv, verbose=1, n_jobs=1)
    model = gs.fit(train_features, train_labels)
    model_score = model.score(test_features, test_labels)

    # Single model with defaults
    s_classifier = svm.SVC(cache_size=cache_size)
    s_model = s_classifier.fit(train_features, train_labels)
    #print model
    s_model_score = s_model.score(test_features, test_labels)

    # Save the best model for final predictions (assume it will be a CV model)
    if model_score > best_score:
        best_feats = feat_name
        best_score = model_score
        best_model = model
        best_params = model.best_params_
        best_features = test_features

    # Save stats on all models run
    model_results.append({
        "feat_name": feat_name,
        "grid_scores": model.grid_scores_,
        "model_params": model.best_params_,
        "model_score": model_score,
        "s_model_score": s_model_score
    })


predictions = best_model.predict(best_features)

#print best_model
print "Best features:", best_feats
print "Best parameters:", best_params
print "Best score:", best_score

# Save all results for graphing later
with open('results_colectores.pickle', 'w') as f:  #los resultados se guardan en un archivo pickle (se codifica la estructura de datos)
    pickle.dump([model_results, df, predictions, best_score, best_params, best_features, best_model], f)

#print(f)

results = pickle.load(open("results_colectores.pickle", "rb"))


model_results = results[0]
df = results[1]
predictions = results[2]
best_score = results[3]
best_params = results[4]
best_features = results[5]
best_model = results[6]
print "Loaded"


print "Best score:", best_score
#print "Best features:", best_features
print "Best params:", best_params



df_test = df[(df["is_test"] == True)] #devuelve los datos que son de prueba, donde is_test = true
df_test["prediction"] = predictions  #agrega la columna predictions al df de prueba
#revisar por qué manda error. cí copia la columna a l df test
#print df_test.head()
# Compare the percent correct to the results from earlier to make sure things are lined up right
print "Calculated accuracy:", sum(df_test["label"] == df_test["prediction"]) / float(len(df_test))
print "Model accuracy:", best_score


df_correct = df_test[(df_test["label"] == df_test["prediction"])] #devuleve los rows cuando label = prediction
df_incorrect = df_test[(df_test["label"] != df_test["prediction"])] #devuelve los rows cuando ñabel es distinto de prediction

print "Correct predictions:", df_correct.groupby(["label"])["prediction"].count()  #imprime el conteo de etiquetas predecidas cprrectamente
print "Incorrect predictions:", df_incorrect.groupby(["label"])["prediction"].count() #imprime el contep de etiquetas predecidas incorrectamente



print df_correct.describe()
print df_incorrect.describe()


#crea d3_data como diccionario a partir de model result
d3_data = {}
for m in model_results:
    d3_data[m["feat_name"]] = {}  
    d3_data[m["feat_name"]]["C"] = []
    d3_data[m["feat_name"]]["G"] = []
    d3_data[m["feat_name"]]["S"] = []
    #print m["feat_name"], m["model_params"], m["model_score"]
    for s in m["grid_scores"]:
        d3_data[m["feat_name"]]["C"].append(s[0]["C"])
        d3_data[m["feat_name"]]["G"].append(s[0]["gamma"])
        d3_data[m["feat_name"]]["S"].append(s[1])
        
        
        
        
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from matplotlib import pylab
pylab.rcParams['figure.figsize'] = (10.0, 8.0)

def d3_plot(X, Y, Z):
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.set_xlabel("C", weight="bold", size="xx-large")
    ax.set_xticks([0, 5000, 10000, 15000])
    ax.set_xlim(0, max(X))
    ax.set_ylabel("gamma", weight="bold", size="xx-large")
    ax.set_yticks([0, 1.5, 3, 4.5])
    ax.set_ylim(0, max(Y))
    ax.set_zlabel("Accuracy", weight="bold", size="xx-large")
    #ax.set_zticks([0.5, 0.6, 0.70])
    ax.set_zlim(0.5, 0.75)
    ax.scatter(X, Y, Z, c='b', marker='o')
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
    plt.show()


d3_plot(np.array(d3_data["area"]["C"]), np.array(d3_data["area"]["G"]), np.array(d3_data["area"]["S"]))
d3_plot(np.array(d3_data["line"]["C"]), np.array(d3_data["line"]["G"]), np.array(d3_data["line"]["S"]))
d3_plot(np.array(d3_data["word"]["C"]), np.array(d3_data["word"]["G"]), np.array(d3_data["word"]["S"]))

pg_engine='postgresql+psycopg2://localhost:5432/mlproject'

df_test.to_sql("df_test_colectores", pg_engine)


#df_add_text = pd.read_sql_query("SELECT id, occid, catalogNumber, filename, text FROM hocr_results_prueba", my_engine)

#df_add_text.to_sql("df_add_text", pg_engine)



