from sqlalchemy import create_engine, inspect,text
import pymongo
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("proje_kayitlari.log", encoding='utf-8'), 
        logging.StreamHandler() 
    ]
)

baglanti_yolu = "mysql+pymysql://root:@localhost:3306/okul_projesi"


motor = create_engine(baglanti_yolu)

mongo_istemci = pymongo.MongoClient("mongodb://localhost:27017/")

mongo_db = mongo_istemci["okul_projesi_mongo"]

print("MongoDB'ye bağlantı sağlandı, aktarım için bekliyor!")

print("Veritabanına bağlanmaya hazırım!")
mufettis = inspect(motor)

tablolar = mufettis.get_table_names()

print("--- Veritabanı Analiz Sonucu ---")
print(f"Bulunan Tablolar: {tablolar}")


for tablo_adi in tablolar:
    print(f"\n--- {tablo_adi} Tablosu İnceleniyor ---")
    
    
    kolonlar = mufettis.get_columns(tablo_adi)
    for kolon in kolonlar:
        print(f" - Kolon: {kolon['name']}, Tipi: {kolon['type']}")

    pk = mufettis.get_pk_constraint(tablo_adi)
    print(f" > Primary Key: {pk['constrained_columns']}")

    fk_listesi = mufettis.get_foreign_keys(tablo_adi)
    for fk in fk_listesi:
        print(f" > Foreign Key: {fk['constrained_columns']} -> Hedef: {fk['referred_table']}.{fk['referred_columns']}")

        print(f" > {tablo_adi} verileri MongoDB'ye aktarılıyor...")
    
    
    with motor.connect() as baglanti:
        # SQL sorgusu çalıştır
        sonuc = baglanti.execute(text(f"SELECT * FROM {tablo_adi}"))
        # Verileri "liste" ve "sözlük" yapısına çevir (JSON gibi)
        satirlar = [dict(satir) for satir in sonuc.mappings()]
        
    
    if satirlar:
        koleksiyon = mongo_db[tablo_adi]
        # Tekrar çalıştırılabilir (Idempotent) olması için önce temizleyelim 
        koleksiyon.delete_many({}) 
        # Verileri ekle
        koleksiyon.insert_many(satirlar)
        print(f" > {len(satirlar)} adet veri başarıyla aktarıldı.")
    else:
        print(" > Tablo boş, aktarılacak veri bulunamadı.")    

    
    indexler = mufettis.get_indexes(tablo_adi)
    for idx in indexler:
        print(f" > Index Bulundu: {idx['name']} (Kolonlar: {idx['column_names']})")

    
    kisitlamalar = mufettis.get_check_constraints(tablo_adi)
    for kisit in kisitlamalar:
        print(f" > Constraint (Kısıtlama) Bulundu: {kisit['name']}")
        print("\n--- Karmaşık Yapılar Analiz Ediliyor ---")


with motor.connect() as baglanti:
    # Trigger tespiti
    trigger_sorgu = text("SHOW TRIGGERS")
    triggerlar = baglanti.execute(trigger_sorgu).fetchall()
    print(f"Bulunan Trigger Sayısı: {len(triggerlar)}")

    
    prosedur_sorgu = text("SHOW PROCEDURE STATUS WHERE Db = 'okul_projesi'")
    prosedurler = baglanti.execute(prosedur_sorgu).fetchall()
    print(f"Bulunan Stored Procedure Sayısı: {len(prosedurler)}")



rapor_notlari = [
    "Triggerlar: MongoDB'de doğrudan karşılığı yok (Uygulama katmanında çözülmeli).",
    "Stored Procedureler: MongoDB'de yok (Python tarafında fonksiyon olarak yazılmalı).",
    "Foreign Keyler: MongoDB'de 'Reference' veya 'Embedded Document' olarak manuel yönetilmeli."
]

logging.info("\n--- RAPOR İÇİN TEKNİK NOTLAR ---")
for not_item in rapor_notlari:
    logging.info(not_item)


def analiz_ve_oneriler(tur, isim):
    """Bulunan karmaşık yapılar için MongoDB dönüşüm önerileri sunar."""
    oneriler = {
        "Trigger": (
            "Gerekçe: MongoDB veritabanı seviyesinde 'native trigger' mekanizmasına sahip değildir.\n"
            "Öneri: Uygulama katmanında (Python/Middleware) kontrol edilmeli veya MongoDB 'Change Streams' kullanılmalıdır."
        ),
        "Stored Procedure": (
            "Gerekçe: MongoDB doküman tabanlıdır ve sunucu tarafında SQL benzeri prosedürleri çalıştırmaz.\n"
            "Öneri: Bu mantık uygulama koduna (Business Logic) taşınmalı veya MongoDB 'Aggregation Pipeline' ile simüle edilmelidir."
        ),
        "Constraint": (
            "Gerekçe: MySQL'deki 'Check Constraint' yapısı MongoDB'de şemadan bağımsızlık nedeniyle farklı işler.\n"
            "Öneri: MongoDB 'Schema Validation' (JSON Schema) özelliği ile koleksiyon seviyesinde kısıtlama eklenmelidir."
        )
    }
    logging.info(f"\n[ANALİZ] {tur} Tespit Edildi: {isim}")
    logging.info(f"{oneriler.get(tur, 'Genel uygulama katmanı çözümü önerilir.')}")


with motor.connect() as conn:
    # Trigger Analizi
    trig_res = conn.execute(text("SHOW TRIGGERS")).fetchall()
    for tr in trig_res:
        analiz_ve_oneriler("Trigger", tr[0])

    # Prosedür Analizi
    proc_res = conn.execute(text(f"SHOW PROCEDURE STATUS WHERE Db = 'okul_projesi'")).fetchall()
    for pr in proc_res:
        analiz_ve_oneriler("Stored Procedure", pr[1])
        
            