from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "cok_gizli_anahtar"

#------------LOGİN İÇİN OLUŞTURULDU--------------------#

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")

        if not username:
            # hata olduğunda yine login sayfasını render edeceğiz
            return render_template("login.html", error="Kullanıcı adı boş olamaz.")

        session["username"] = username
        #ileride kullanıcılara level buralardan eklenecek 
        return redirect(url_for("dashboard"))

    # GET isteğinde direkt login sayfasını göster
    return render_template("login.html")


#------DASHBOARD İÇİN OLUŞTURULDU---------#
@app.route("/dashboard")
def dashboard():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=username)


#-----WORD PRACTİCE (KELİME ALIŞTIRMASI) İÇİN OLUŞTURULDU-------#
@app.route("/practice_word", methods=["GET", "POST"])

def practice_word():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    #elimizde kelime olmadığı süreç için kendimiz kelime atıyoruz(denemek için)

    words = [
        {"english": "apple", "turkish": "elma"},
        {"english": "book", "turkish": "kitap"},
        {"english": "cat", "turkish": "kedi"},
    ]
    current_word = words[0]  # basit demo: hep ilk kelime

    result = None

    if request.method == "POST":
        user_answer =request.form.get("answer", "").strip().lower()
        correct = current_word["turkish"].lower()

        is_correct = (user_answer == correct)
        result = {
            "user_answer": user_answer,
            "correct_answer": correct,
            "is_correct": is_correct
        }

        #db eklenince burası gidecek dbye ekenecek

    return render_template(
        "practice_word.html",
        username=username,
        word=current_word,
        result=result
    )
    

#-------SeNTENCE VE GRAMMER PRACTİCE----------------#
@app.route("/practice/sentence", methods=["GET","POST"])
def practice_sentence():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    
    feedback = None
    user_sentence = None

    if request.method =="POST":
        user_sentence = request.form.get("sentence", "").strip()

        if user_sentence:
            #llmi henüz dahil etmedik edince eklicez şimdilik dummy feedback

            feedback = (
                "bu sadece bir geri bildirim"
                "normalde buraya llm ile cümle analizi gelecek"
            )
            
    return render_template(
        "practice_sentence.html",
        username = username,
        user_sentence = user_sentence,
        feedback=feedback

    )


#-------PRONUNCATİON PRACTİCE-----------#
@app.route("/pronunciation", methods=["GET", "POST"])
def pronunciation():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    

    target_word ="apple"
    score =None 
    info = None

    if request.method == "POST":
        #şimdilik gerçek ses yok demo butonu ile skor gösteriliyor 
        # buraya sonrada file yükleme artı stt artı skor hesabı gelecek

        score = 82
        info = "şimdilik demo skor sonrasında ses analizi ile hesaplanacak"

    return render_template(
        "pronunciation.html",
        username=username,
        target_word=target_word,
        score=score,
        info=info
    )
    
if __name__ == "__main__":
    app.run(debug=True)




