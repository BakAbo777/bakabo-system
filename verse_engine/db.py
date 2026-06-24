"""DB init e seed — eseguito all'avvio FastAPI."""
import sqlite3
from pathlib import Path
from verse_engine.config import settings

ROOT = Path(__file__).parent.parent
SCHEMA = ROOT / "data" / "schema.sql"

POETS = [
    {"slug":"celan","name":"Paul Celan","country_code":"RO","era":"1920-1970","city":"Parigi",
     "year_birth":1920,"year_death":1970,"rep_poem_title":"Todesfuge","rep_poem_excerpt":"Schwarze Milch der Frühe wir trinken sie abends",
     "score_image":5,"score_voice":5,"score_tension":5,"score_bks":5,"score_body":4},
    {"slug":"rilke","name":"Rainer Maria Rilke","country_code":"CZ","era":"1875-1926","city":"Praga",
     "year_birth":1875,"year_death":1926,"rep_poem_title":"Arcaico torso di Apollo","rep_poem_excerpt":"Non possiamo sapere la sua testa leggendaria.",
     "score_image":5,"score_voice":5,"score_tension":4,"score_bks":5,"score_body":5},
    {"slug":"rimbaud","name":"Arthur Rimbaud","country_code":"FR","era":"1854-1891","city":"Charleville",
     "year_birth":1854,"year_death":1891,"rep_poem_title":"Le Bateau ivre","rep_poem_excerpt":"Comme je descendais des Fleuves impassibles",
     "score_image":5,"score_voice":5,"score_tension":5,"score_bks":4,"score_body":4},
    {"slug":"lorca","name":"Federico García Lorca","country_code":"ES","era":"1898-1936","city":"Granada",
     "year_birth":1898,"year_death":1936,"rep_poem_title":"Romance sonámbulo","rep_poem_excerpt":"Verde que te quiero verde. Verde viento. Verdes ramas.",
     "score_image":5,"score_voice":5,"score_tension":4,"score_bks":4,"score_body":5},
    {"slug":"basho","name":"Matsuo Bashō","country_code":"JP","era":"1644-1694","city":"Ueno",
     "year_birth":1644,"year_death":1694,"rep_poem_title":"Lo stagno antico","rep_poem_excerpt":"Un vecchio stagno — una rana vi salta — suono d'acqua.",
     "score_image":5,"score_voice":4,"score_tension":5,"score_bks":5,"score_body":5},
    {"slug":"plath","name":"Sylvia Plath","country_code":"US","era":"1932-1963","city":"Boston",
     "year_birth":1932,"year_death":1963,"rep_poem_title":"Lady Lazarus","rep_poem_excerpt":"Out of the ash I rise with my red hair",
     "score_image":5,"score_voice":5,"score_tension":5,"score_bks":4,"score_body":4},
    {"slug":"ginsberg","name":"Allen Ginsberg","country_code":"US","era":"1926-1997","city":"New York",
     "year_birth":1926,"year_death":1997,"rep_poem_title":"Howl","rep_poem_excerpt":"I saw the best minds of my generation destroyed by madness",
     "score_image":4,"score_voice":5,"score_tension":4,"score_bks":3,"score_body":4},
    {"slug":"dickinson","name":"Emily Dickinson","country_code":"US","era":"1830-1886","city":"Amherst",
     "year_birth":1830,"year_death":1886,"rep_poem_title":"Because I could not stop for Death","rep_poem_excerpt":"He kindly stopped for me — The Carriage held but just Ourselves",
     "score_image":5,"score_voice":5,"score_tension":5,"score_bks":5,"score_body":4},
    {"slug":"montale","name":"Eugenio Montale","country_code":"IT","era":"1896-1981","city":"Genova",
     "year_birth":1896,"year_death":1981,"rep_poem_title":"Meriggiare pallido e assorto","rep_poem_excerpt":"Meriggiare pallido e assorto presso un rovente muro d'orto",
     "score_image":5,"score_voice":4,"score_tension":5,"score_bks":5,"score_body":4},
    {"slug":"neruda","name":"Pablo Neruda","country_code":"CL","era":"1904-1973","city":"Parral",
     "year_birth":1904,"year_death":1973,"rep_poem_title":"Ode alla mia tuta","rep_poem_excerpt":"Ogni mattina mi aspetti sul tuo gancio",
     "score_image":4,"score_voice":5,"score_tension":3,"score_bks":4,"score_body":5},
    {"slug":"szymborska","name":"Wisława Szymborska","country_code":"PL","era":"1923-2012","city":"Kórnik",
     "year_birth":1923,"year_death":2012,"rep_poem_title":"Vista con un grano di sabbia","rep_poem_excerpt":"Chiamiamo un grano di sabbia, un grano di sabbia.",
     "score_image":4,"score_voice":5,"score_tension":4,"score_bks":5,"score_body":4},
    {"slug":"leopardi","name":"Giacomo Leopardi","country_code":"IT","era":"1798-1837","city":"Recanati",
     "year_birth":1798,"year_death":1837,"rep_poem_title":"L'Infinito","rep_poem_excerpt":"Sempre caro mi fu quest'ermo colle",
     "score_image":4,"score_voice":5,"score_tension":4,"score_bks":4,"score_body":4},
    {"slug":"bukowski","name":"Charles Bukowski","country_code":"US","era":"1920-1994","city":"Los Angeles",
     "year_birth":1920,"year_death":1994,"rep_poem_title":"bluebird","rep_poem_excerpt":"there's a bluebird in my heart that wants to get out",
     "score_image":4,"score_voice":5,"score_tension":4,"score_bks":3,"score_body":4},
    {"slug":"rumi","name":"Rumi","country_code":"AF","era":"1207-1273","city":"Balkh",
     "year_birth":1207,"year_death":1273,"rep_poem_title":"Il canto del flauto","rep_poem_excerpt":"Ascolta il flauto di canna, racconta separazioni",
     "score_image":4,"score_voice":5,"score_tension":4,"score_bks":4,"score_body":4},
    {"slug":"whitman","name":"Walt Whitman","country_code":"US","era":"1819-1892","city":"New York",
     "year_birth":1819,"year_death":1892,"rep_poem_title":"Foglie d'erba","rep_poem_excerpt":"Io mi celebro e mi canto",
     "score_image":4,"score_voice":5,"score_tension":3,"score_bks":4,"score_body":4},
    {"slug":"cavafy","name":"Konstantinos Kavafis","country_code":"GR","era":"1863-1933","city":"Alessandria",
     "year_birth":1863,"year_death":1933,"rep_poem_title":"Itaca","rep_poem_excerpt":"Quando ti metterai in viaggio per Itaca",
     "score_image":4,"score_voice":5,"score_tension":4,"score_bks":4,"score_body":4},
    {"slug":"sappho","name":"Saffo","country_code":"GR","era":"-630 -570","city":"Lesbo",
     "year_birth":-630,"year_death":-570,"rep_poem_title":"Ode ad Afrodite","rep_poem_excerpt":"Immortale Afrodite, figlia di Zeus",
     "score_image":4,"score_voice":5,"score_tension":4,"score_bks":4,"score_body":5},
    {"slug":"pasolini","name":"Pier Paolo Pasolini","country_code":"IT","era":"1922-1975","city":"Bologna",
     "year_birth":1922,"year_death":1975,"rep_poem_title":"Le ceneri di Gramsci","rep_poem_excerpt":"Non è di maggio questa impura aria",
     "score_image":5,"score_voice":5,"score_tension":5,"score_bks":5,"score_body":4},
    {"slug":"cummings","name":"e.e. cummings","country_code":"US","era":"1894-1962","city":"Cambridge",
     "year_birth":1894,"year_death":1962,"rep_poem_title":"l(a","rep_poem_excerpt":"l(a le af fa ll s) one l iness",
     "score_image":5,"score_voice":5,"score_tension":5,"score_bks":5,"score_body":5},
    {"slug":"ungaretti-mattina","name":"Ungaretti (M'illumino)","country_code":"IT","era":"1888-1970","city":"Alessandria d'Egitto",
     "year_birth":1888,"year_death":1970,"rep_poem_title":"M'illumino d'immenso","rep_poem_excerpt":"M'illumino d'immenso",
     "score_image":5,"score_voice":5,"score_tension":5,"score_bks":5,"score_body":5},
    {"slug":"ungaretti-soldati","name":"Ungaretti (Soldati)","country_code":"IT","era":"1888-1970","city":"Alessandria d'Egitto",
     "year_birth":1888,"year_death":1970,"rep_poem_title":"Soldati","rep_poem_excerpt":"Si sta come d'autunno sugli alberi le foglie",
     "score_image":5,"score_voice":5,"score_tension":5,"score_bks":5,"score_body":5},
]


def init_db() -> None:
    db_path = Path(settings.verse_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    count = conn.execute("SELECT COUNT(*) FROM poet_archive").fetchone()[0]
    if count == 0:
        conn.executemany("""
            INSERT OR IGNORE INTO poet_archive
              (slug,name,country_code,era,city,year_birth,year_death,
               rep_poem_title,rep_poem_excerpt,
               score_image,score_voice,score_tension,score_bks,score_body)
            VALUES
              (:slug,:name,:country_code,:era,:city,:year_birth,:year_death,
               :rep_poem_title,:rep_poem_excerpt,
               :score_image,:score_voice,:score_tension,:score_bks,:score_body)
        """, POETS)
        conn.commit()

    conn.close()
