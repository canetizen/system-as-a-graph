# Sistem/Alt Sistem Şartnamesi (SSS): System as a Graph (SaaG)

**Tanım:** System as a Graph (SaaG) Sayısal Sistem Modeli, mimari dijital ikiz yaklaşımıyla geliştirilmiş, sistem uygulamalarını fiilen çalıştırmaksızın, sistemin yapısal ve ilişkisel mimarisini düğüm-ilişki temsiliyle modelleyen statik bir sayısal sistem modelidir. Bu modelde yazılım birimleri, arakatman ve haberleşme servisleri, işlemci/konsol birimleri, topic ve mesaj gibi sistem varlıkları düğüm; aralarındaki bağımlılık, yayımlama ve tüketme bağıntıları ise ilişki olarak temsil edilir. Modelin davranışsal analizlere imkân tanıyan boyutu, bileşenlerin koşumuyla değil; saha kayıtlarından veya senaryo üretecinden türetilen Analitik Değerlendirme Verisinin bu model üzerine bindirilmesiyle sağlanır.

**Tablo 1. SSS İster Dağılımı**

| No | Bileşen | Kısaltma | İster Sayısı |
|---|---|---|---|
| 1 | Model Kurulum Verisi Üretimi | SaaG-MKV | 19 |
| 2 | Senaryo Üreteci | SaaG-SUR | 7 |
| 3 | Saha Kayıtları Veri Tabanı | SaaG-SKV | 6 |
| 4 | Analitik Veri Hazırlama | SaaG-AVH | 6 |
| 5 | Düğüm-İlişki Tabanlı Çekirdek Sistem Modeli | SaaG-CSM | 20 |
| 6 | Tasarım Doğrulama, Analiz ve Değerlendirme | SaaG-DAD | 54 |
| **TOPLAM** | | | **112** |

**Amaç:** Modelin birincil amacı mimari doğrulamadır. Bu kapsamdan yapısal/döngüsel bağımlılıklar, yayımcı/tüketici eşleşmeleri, topic servis kalite parametrelerinin (QoS) uygunluğu, sistemde yer alan donanımların kapasite uygunluğu (CPU çekirdek adedi, RAM boyutu, ağ bant genişliği vb.) ve mimari kurallara aykırı tasarım örüntüleri tasarım aşamasında statik olarak denetlenir. Mimari doğrulama, tasarımda öngörülen mimari ile saha verisinde gözlemlenen çalışma-zamanı yapısı arasındaki sapmaların (architectural drift) tespitini de kapsar. Mimari doğrulamanın yanı sıra model, kurgusal senaryo analizlerine olanak tanır; kullanıcı, yapısal bütünlüğü bozmadan düğüm/ilişki ekleyip çıkararak ya da öznitelikleri değiştirerek deneysel tasarım kurguları oluşturabilir. Bu kurgusal senaryolarda bir varlığın devre dışı kalması, mesaj yoğunluğunun artması veya bant genişliğinin daralması gibi durumların bağımlı varlıklara yayılımı ve mimari üzerindeki etkileri analitik olarak değerlendirilir. Böylelikle Sayısal Sistem Modeli, henüz yazılım birimlerinin hedef ortama kurulumları yapılmadan tasarım kararlarının ve değişikliklerinin mimari sonuçlarını öngörmeye yönelik, tekrarlanabilir bir doğrulama ortamı sağlar.

---

## 1. Model Kurulum Verisi Üretimi

1. SaaG, Sayısal Sistem Modeli'nin oluşturulmasına esas verilerin kontrollü, izlenebilir, doğrulanabilir ve model inşası süreçlerine aktarılabilir şekilde üretilmesini sağlayan Model Kurulum Verisi Üretimi (SaaG-MKV) bileşenine sahip olacaktır.

2. SaaG-MKV, Model Kurulum Verisi üretimi maksadıyla en az aşağıdaki dış veri kaynaklarına erişim sağlayabilecek ve bu kaynaklardan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir:
   1. Sistem konfigürasyon yönetimi veri tabanı,
   2. Sistem yazılım birimleri ve kurulum betikleri kaynak kodu deposu,
   3. Sistem Yazılım Birimleri Paket Deposu,
   4. Sistem Ağ Topolojisi Veri Kaynağı,

3. SaaG-MKV, sistem ağ topolojisi verisini aşağıdaki yöntemlerden biri ile alabilecektir:
   1. Detayları kritik tasarım aşamasında belirlenecek dış bir veri kaynağından (dosya, veri tabanı vb.) otomatik olarak,
   2. Kullanıcının ağ topolojisi parametrelerini manuel olarak girmesi yoluyla.

4. SaaG-MKV, her veri kaynağı için kaynak tipi, kaynak adı, erişim yöntemi, bağlantı adresi ve bağlantı için gerekli kullanıcı bilgilerini kullanıcı tarafından tanımlanabilir ve kaydedilebilir ayar bilgisi olarak yönetecektir.

5. SaaG-MKV, veri alım işlemlerini proje bilgisi, platform bilgisi ve sistem sürüm numarası ile ilişkilendirilmiş şekilde yürütecektir.

6. SaaG-MKV, konfigürasyon yönetimi veri tabanından mevcut proje bilgilerini alabilecektir.

7. SaaG-MKV, konfigürasyon yönetimi veri tabanından seçilen projeye ait platform bilgilerini alabilecektir.

8. SaaG-MKV, konfigürasyon yönetimi veri tabanından seçilen proje ve platforma ait sistem sürüm bilgilerini alabilecektir.

9. SaaG-MKV, konfigürasyon yönetimi veri tabanından alınan sistem sürüm bilgileri içerisindeki yürürlükteki güncel sürüm bilgisini işaretleyecektir.

10. SaaG-MKV, seçilen proje, platform ve sürüm bilgisine göre sistem ortamında çalışacak yazılım birimlerine ait isim ve sürüm bilgilerini "Yazılım Birimi Sürüm Envanteri" olarak kayıt altına alacaktır.

11. SaaG-MKV, hedef ortama kurulması değerlendirilen yazılım biriminin aday sürümü ile seçilen sistem sürümünde tanımlı diğer yazılım birimi sürümlerini kullanarak Yazılım Birimi Sürüm Envanterini güncelleyecek ve kayıt altına alacaktır.

12. SaaG-MKV, konfigürasyon yönetimi veri tabanından alınan verilerde eksiklik, erişim hatası veya format uyumsuzluğu tespit edilmesi durumunda veri alım sürecini hata durumu ile işaretleyecektir.

13. SaaG-MKV, kaynak kodu deposu üzerinden Yazılım Birimi Sürüm Envanteri kapsamındaki yazılım birimlerine ait kaynak kodu, kurulum betikleri ve konfigürasyon dosyalarına erişerek sisteme aktaracaktır.

14. SaaG-MKV, kaynak kodu deposundan alınan her dosya için dosya adı, dosya yolu, paket/versiyon bilgisi ve güncelleme zaman damgasını kayıt altına alacaktır.

15. SaaG-MKV, kaynak kodu deposundan alınması zorunlu olan ve detayları kritik tasarım aşamasında belirlenecek dosyalardan herhangi birinin eksik olması durumunda veri alım sürecini "eksik veri" durumu ile raporlayacaktır.

16. SaaG-MKV, kaynak kodu deposundan alınan dosyalarda erişim, yetki veya bütünlük hatası oluşması durumunda ilgili hatayı sergileyecek ve kayıt altına alacaktır.

17. SaaG-MKV, alınan veya elle girilen tüm kaynak verileri için model inşası kapsamında gerekli alan varlığı kontrolü gerçekleştirecektir.

18. SaaG-MKV, kontrol sonucu başarısız olan her veri için hata nedeni, kaynak adı, kaynak tipi, ilişkili proje/platform bilgisi ve hata zamanı bilgisini kayıt altına alacaktır.

19. SaaG-MKV, doğrulama kontrollerinden geçen kaynak verileri model inşası sürecine aktarılmaya hazır hale getirecek ve Model Kurulum Verisi dosyası olarak kaydedecektir.

---

## 2. Senaryo Üreteci

1. SaaG, saha kayıtlarına ihtiyaç duyulmaksızın, kullanıcı tarafından belirlenen senaryo girdilerine göre sentetik veri üretebilen Senaryo Üreteci (SaaG-SUR) bileşenine sahip olacaktır.

2. SaaG-SUR, detayları kritik tasarım aşamasında belirlenecek sistem genelindeki tüm simülasyon işlemlerinin veri kaynağı olarak işlev görecek ve simülasyon süreçlerinde kullanılacak sentetik verileri üretecektir.

3. SaaG-SUR, kullanıcının senaryo üretimi için gerekli senaryo kapsamı, senaryo türü, zaman aralığı, veri yoğunluğu ve üretilecek veri türlerini belirleyebilmesini sağlayacaktır.

4. SaaG-SUR, kullanıcı girdilerine göre yazılım birimlerinin kullandığı topic/mesaj veri şemasına, alan adlandırmasına ve değer aralığı kısıtlarına uygun eşdeğer yapıda sentetik veri üretebilecektir.

5. SaaG-SUR, üretilen sentetik verileri senaryo adı, üretim zamanı, ilişkili proje bilgisi, platform bilgisi ve sistem sürüm numarası ile kayıt altına alacaktır.

6. SaaG-SUR, sentetik verinin üretiminde kullanılan kullanıcı girdilerini izlenebilir şekilde kayıt altına alacaktır.

7. SaaG-SUR, üretilen sentetik veriyi Analitik Veri Hazırlama bileşenine aktarılmaya hazır hale getirecektir.

---

## 3. Saha Kayıtları Veri Tabanı

1. SaaG, sistemin kurulu olduğu platformlardan sistem veri kayıt mekanizması ile alınan sistem veri kayıtlarının ve telemetri verilerinin "Sistem Saha Kayıtları" olarak merkezi biçimde depolanması ve yönetilmesi maksadıyla bir Saha Kayıtları Veri Tabanına (SaaG-SKV) sahip olacaktır.

2. SaaG-SKV, kullanıcının sistem saha ortamından alınan telemetri ve sistem veri kayıtlarını Saha Kayıtları Veri Tabanına kontrollü, izlenebilir şekilde yükleyebilmesini sağlayacak; yüklenen kayıtları ilgili proje bilgisi, platform bilgisi ve sistem sürüm numarası ile ilişkilendirerek kaydedecektir.

3. SaaG-SKV, yüklenen Sistem Saha Kayıtlarını kayıt kaynağı, yükleme zamanı, ilişkili proje, platform ve sistem sürüm bilgisiyle birlikte izlenebilir şekilde kayıt altına alacaktır.

4. SaaG-SKV, kullanıcının mevcut Sistem Saha Kayıtlarını proje, platform, sistem sürümü, kayıt kaynağı veya yükleme zamanı ölçütlerine göre listeleyebilmesini, arayabilmesini ve seçebilmesini sağlayacaktır.

5. SaaG-SKV, yükleme sırasında tespit edilen format uyumsuzluğu, bütünlük hatası veya eksik alan durumlarını raporlayacak ve kayıt altına alacaktır.

6. SaaG-SKV, detayları kritik tasarım aşamasında belirlenecek disk kapasitesine sahip bir depolama donanımı üzerinde çalışacaktır.

---

## 4. Analitik Veri Hazırlama

1. SaaG, analiz, doğrulama ve simülasyon süreçlerinde kullanılacak Analitik Değerlendirme Verisinin kontrollü, izlenebilir, doğrulanabilir ve Çekirdek Sistem Modeline aktarılabilir şekilde hazırlanmasını sağlayan Analitik Veri Hazırlama (SaaG-AVH) bileşenine sahip olacaktır.

2. SaaG-AVH, Analitik Değerlendirme Verisinin hazırlanmasında kullanılacak Sistem Saha Kayıtlarını Saha Kayıtları Veri Tabanından alabilecektir.

3. SaaG-AVH, Analitik Değerlendirme Verisini oluşturmak için gerekli olan verileri Senaryo Üreteci tarafından üretilen sentetik verileri alabilecektir.

4. SaaG-AVH, Sistem Saha Kayıtları veya Senaryo Üreteci tarafından sağlanan sentetik verileri işleyip uygun şekilde ilişkilendirerek detayları kritik tasarım aşamasında belirlenecek Analitik Değerlendirme Verisini üretecek ve Çekirdek Sistem Modeline iletilecektir.

5. SaaG-AVH, Sistem Saha Kayıtlarında format uyumsuzluğu veya okunamayan veri tespit edilmesi durumunu raporlayacak ve kayıt altına alacaktır.

6. SaaG-AVH, Senaryo Üreteci tarafından sağlanan sentetik veride format uyumsuzluğu, okunamayan veri veya eksik alan tespit edilmesi durumunu raporlayacak ve kayıt altına alacaktır.

---

## 5. Düğüm-İlişki Tabanlı Çekirdek Sistem Modeli

1. SaaG, Model Kurulum Verisini kullanarak sistemin yapısal ve ilişkisel temsilini bir düğüm-ilişki yapısında oluşturacak; Analitik Değerlendirme Verisini modeldeki ilgili sistem varlıkları ile bunlar arasındaki bağlantılarla eşleştirerek statik analiz, doğrulama ve simülasyon süreçlerinde kullanılabilir hâle getirecek Düğüm-İlişki Tabanlı Çekirdek Sistem Modeli (SaaG-CSM) bileşenine sahip olacaktır.

2. SaaG-CSM, Model Kurulum Verisi Üretimi bileşeni tarafından oluşturulan Model Kurulum Verisini girdi olarak alabilecektir.

3. SaaG-CSM, Çekirdek Sistem Modelinin inşası öncesinde Model Kurulum Verisinin biçim, şema, bütünlük ve zorunlu alan kontrollerini gerçekleştirecektir.

4. SaaG-CSM, kontrolden geçen Model Kurulum Verisini düğüm-ilişki tabanlı Çekirdek Sistem Modeline dönüştürecektir.

5. SaaG-CSM, Çekirdek Sistem Modelini ilgili proje, platform ve sistem sürüm bilgisi ile ilişkilendirilmiş şekilde oluşturacaktır.

6. SaaG-CSM, Model Kurulum Verisinde bulunan en az aşağıdaki yapısal sistem varlıklarını düğüm-ilişki yapısında düğüm olarak temsil edecektir:
   1. Sistem,
   2. Yazılım Segmenti,
   3. Yazılım Kırılım Öğesi (CSCI),
   4. Yazılım Komponenti (CSC),
   5. Yazılım Birimi (CSU),
   6. Rol,
   7. Topic,
   8. Mesaj,
   9. Operatör Konsolu ve İşlemci Birimleri,
   10. Ağ bileşenleri
   11. Arakatman Servisleri,
   12. Haberleşme Teknolojilerine ait Servisler.

7. SaaG-CSM, yapısal sistem varlıkları arasındaki en az aşağıdaki ilişki türlerini düğüm-ilişki yapısında ilişki olarak temsil edecektir:
   1. Operatör Konsolu ve İşlemci Birimleri üzerinde çalışma,
   2. Arakatman ve İletişim Servislerini kullanma,
   3. Veri yayımlama,
   4. Veri tüketme,
   5. Kütüphane veya yazılım birimine bağımlı olma.
   6. Yazılım biriminin bir role tanımlanması.

8. SaaG-CSM, sistem yazılım birimlerine ait işlemci çekirdek tahsisi (CPU allocation), işletim sistemi ayarları ve çalışma zamanı ortamı yapılandırmalarını (JVM vb.) düğüm-ilişki yapısı üzerinde sorgulanabilir öznitelikler olarak temsil edecektir.

9. SaaG-CSM, Çekirdek Sistem Modelinin oluşturulması sırasında tespit edilen eksik varlık, geçersiz ilişki hatalarını raporlayacak ve kayıt altına alacaktır.

10. SaaG-CSM, Analitik Veri Hazırlama bileşeni tarafından üretilen Analitik Değerlendirme Verisini girdi olarak alabilecektir.

11. SaaG-CSM, Analitik Değerlendirme Verisini ilgili proje, platform, sistem sürümü ve Çekirdek Sistem Modeli ile ilişkilendirecek; veride bulunan kayıt, telemetri ve sentetik verileri ilgili düğümlerle ve ilişkilerle eşleştirerek düğüm-ilişki yapısına bağlayacaktır.

12. SaaG-CSM, Analitik Değerlendirme Verisinin Sistem Saha Kayıtları veya Senaryo Üreteci tarafından sağlanan sentetik verilerden hangisi kullanılarak üretildiği bilgisini koruyacaktır.

13. SaaG-CSM, Analitik Değerlendirme Verisini Çekirdek Sistem Modelindeki düğümleri ve ilişkileri değiştirmeden modele bağlayacak ve Çekirdek Sistem Modeli verileri ile Analitik Değerlendirme Verilerinin birbirinden ayrıştırılabilir şekilde yönetilmesini sağlayacaktır.

14. SaaG-CSM, Analitik Değerlendirme Verisinde karşılığı bulunamayan düğüm veya ilişki kayıtlarını raporlayacak ve kayıt altına alacaktır.

15. SaaG-CSM, oluşturulan Çekirdek Sistem Modeli için kullanılan Model Kurulum Verisi dosyasını, model oluşturma zamanını, proje bilgisini, platform bilgisini, sistem sürüm numarasını ve model durumunu kayıt altına alacaktır.

16. SaaG-CSM, Çekirdek Sistem Modelini Tasarım Doğrulama, Analiz ve Değerlendirme bileşeninin kullanımına sunacaktır.

17. SaaG-CSM, Tasarım Doğrulama, Analiz ve Değerlendirme bileşeninin düğümlere, ilişkilere ve bunlarla ilişkilendirilmiş Analitik Değerlendirme Verilerine erişebilmesini sağlayacaktır.

18. SaaG-CSM, aynı Çekirdek Sistem Modeli üzerinde birden fazla kullanıcı oturumu tarafından eşzamanlı olarak gerçekleştirilen okuma/yazma işlemlerini, model bütünlüğünü ve sorgu sonuçlarının tutarlılığını bozmadan karşılayacaktır.

19. SaaG-CSM, üretim dağıtım hattındaki işlemler ile kritik tasarım aşamasında belirlenecek sayıda kullanıcının analiz ve simülasyon işlemlerini eşzamanlı ve birbirinden bağımsız olarak yürütecek; işlemlerin birbirini etkilemesini engelleyecektir.

20. SaaG-CSM, hedef ortama kurulması değerlendirilen yazılım biriminin aday sürümü ile hedef sistem sürümündeki diğer yazılım birimlerini kullanarak işleme özel yeni bir Çekirdek Sistem Modeli oluşturacaktır.

---

## 6. Tasarım Doğrulama, Analiz ve Değerlendirme

1. SaaG, kullanıcının sistem bileşenleriyle doğrudan etkileşim kurmasını ve model üzerinde tasarım doğrulama, statik analiz ve değerlendirme işlemlerini gerçekleştirmesini sağlayan Tasarım Doğrulama, Analiz ve Değerlendirme (SaaG-DAD) bileşenine sahip olacaktır.

2. SaaG-DAD, Model Kurulum Verisi Üretimi, Senaryo Üreteci, Analitik Veri Hazırlama ve Çekirdek Sistem Modeli bileşenleriyle etkileşim kurabilecektir.

3. SaaG-DAD, sisteme erişmek isteyen kullanıcıların kullanıcı adı ve parola bilgilerini tanımlı LDAP dizin hizmeti üzerinden doğrulayacak ve yalnızca kimlik doğrulaması başarılı olan kullanıcıların yetkileri kapsamında sisteme erişmesini sağlayacaktır.

4. SaaG-DAD, kullanıcının işlem yapılacak proje, platform ve sistem sürümünü seçebilmesini sağlayacak ve proje ile platform için yürürlükte bulunan güncel sistem sürümünü ayırt edilebilir şekilde gösterecektir.

5. SaaG-DAD, seçilen proje, platform ve sistem sürümüne ait Model Kurulum Verisi dosyalarını kullanıcıya listeleyecek ve kullanıcının kullanılacak dosyayı seçebilmesini sağlayacaktır.

6. SaaG-DAD, kullanıcının Model Kurulum Verisi üretim sürecini başlatabilmesini ve sürecin durumunu devam ediyor, başarılı veya başarısız durumlarından biriyle izleyebilmesini sağlayacaktır.

7. SaaG-DAD, kullanılan tüm veri kaynaklarına ait erişilebilirlik durumlarını kullanıcıya sürekli ve izlenebilir şekilde gösterecektir.

8. SaaG-DAD, Model Kurulum Verisi üretimi sırasında tespit edilen eksik veri, erişim, yetki, biçim veya bütünlük hatalarını kullanıcıya gösterecektir.

9. SaaG-DAD, kullanıcının seçilen Model Kurulum Verisini kullanarak Çekirdek Sistem Modelini oluşturma işlemini başlatabilmesini ve işlem sonucunu başarılı ya da başarısız durumlarından biriyle izleyebilmesini sağlayacaktır.

10. SaaG-DAD, kullanıcının Analitik Değerlendirme Verisinin oluşturulmasında kullanılacak veri kaynağını aşağıdaki seçeneklerden biri olarak belirleyebilmesini sağlayacaktır:
    1. Sistem Saha Kayıtları,
    2. Senaryo Üreteci tarafından sağlanan sentetik veriler.

11. SaaG-DAD, Sistem Saha Kayıtlarının kullanılacağı durumda kullanıcının kullanılacak kayıtları seçebilmesini sağlayacaktır.

12. SaaG-DAD, sentetik verilerin kullanılacağı durumda kullanıcının senaryo kapsamı, senaryo türü, zaman aralığı, veri yoğunluğu ve üretilecek veri türlerine ilişkin girdileri belirleyebilmesini sağlayacaktır.

13. SaaG-DAD, kullanıcının sentetik veri üretim sürecini başlatabilmesini, takip edebilmesini ve üretim sırasında meydana gelen hataları görüntüleyebilmesini sağlayacaktır.

14. SaaG-DAD, kullanıcının Analitik Değerlendirme Verisi üretim sürecini başlatabilmesini, takip edebilmesini ve üretim sırasında meydana gelen hataları görüntüleyebilmesini sağlayacaktır.

15. SaaG-DAD, tasarım doğrulama ve analiz işlemlerini Çekirdek Sistem Modelindeki düğüm ve ilişkileri değiştirmeden gerçekleştirecektir.

16. SaaG-DAD, kullanıcıya Çekirdek Sistem Modeline bağlanan Analitik Değerlendirme Verisinin ilişkili olduğu proje, platform ve sistem sürümü bilgisini gösterecek; veride bulunan kayıt, telemetri ve sentetik verilerin düğümler ve ilişkilerle eşleştirme durumunu raporlayacaktır.

17. SaaG-DAD, kullanıcının Çekirdek Sistem Modelinin yapısal bütünlüğünü bozmadan türetilen bir çalışma modeli üzerinde düğüm ekleme/çıkarma, ilişki ekleme/çıkarma ve düğüm/ilişki özniteliklerini güncelleme gibi yapısal değişiklikler gerçekleştirebilmesini; güncellenen çalışma modeli üzerinde tasarım doğrulama ve analiz işlemleri yürütebilmesini sağlayacaktır.

18. SaaG-DAD, Analitik Değerlendirme Verisi kullanılmaksızın yalnızca Çekirdek Sistem Modeli üzerinde analizler gerçekleştirebilecektir.

19. SaaG-DAD, sistem varlıkları arasındaki yapısal bağımlılıkların, haberleşme bağlantılarının ve çalışma ortamı ilişkilerinin analizini Çekirdek Sistem Modeli üzerinde gerçekleştirebilecektir.

20. SaaG-DAD, topic veri iletimi servis kalite parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacak ve en az aşağıdaki parametreler özelinde uyumsuzlukları tespit edecektir:
    1. Veri Saklama (Durability),
    2. Güvenilirlik (Reliability),
    3. Yaşam Süresi (Lifespan),
    4. Taşıma Önceliği (TransportPriority).

21. SaaG-DAD, topic veri yayımlayıcı ve veri tüketici eşleşmelerini Çekirdek Sistem Modeli üzerinde doğrulayacak ve en az aşağıdaki uyumsuzlukları tespit edecektir:
    1. Veri yayımlayıcısı bulunmayan topic,
    2. Veri tüketicisi bulunmayan topic,
    3. Aynı isimle tanımlanan topiclerin içerik tanımlarının birbirinden farklı olması.

22. SaaG-DAD, kritik tasarım aşamasında belirlenecek haberleşme servisleri üzerinden gerçekleştirilen arakatman harici iletişimlerde kaynak, hedef, mesaj ve iletişim yönü bilgilerinin birbiriyle uyumunu Çekirdek Sistem Modeli üzerinde doğrulayacaktır.

23. SaaG-DAD, sistem yazılım birimlerinin Operatör Konsolu ve İşlemci Birimleri üzerindeki dağılımının detayları kritik tasarım aşamasında belirlenecek yük dengeleme kurallarına uygunluğunu Çekirdek Sistem Modeli üzerinde analiz edecektir.

24. SaaG-DAD, sistem yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacak ve en az aşağıdaki uyumsuzlukları tespit edecektir:
    1. Bir İşlemci Birimi üzerinde tahsis edilen toplam çekirdek sayısının mevcut çekirdek kapasitesini aşması,
    2. Aynı çekirdeklerin birden fazla uygulamaya çakışacak şekilde tahsis edilmesi,
    3. Yüksek performansla çalışması gereken uygulamalara özel (dedicated) çekirdek tahsis edilmemiş olması.

25. SaaG-DAD, işlemci/konsol birimlerinde çalışan işletim sistemi ayarlarının detayları kritik tasarım aşamasında belirlenecek kurallara ve yapılan işlemci çekirdek tahsisine uygunluğunu Çekirdek Sistem Modeli üzerinde denetleyecektir.

26. SaaG-DAD, sistem yazılım birimlerine ait çalışma zamanı ortamı yapılandırmalarındaki bellek tahsis parametrelerinin, detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacaktır.

27. SaaG-DAD, işlemci çekirdek tahsisi, işletim sistemi ayarları ve çalışma zamanı ortamı yapılandırmaları arasındaki tutarsızlıklardan kaynaklanabilecek kaynak yığılması ve darboğaz oluşturabilecek durumları Çekirdek Sistem Modeli üzerinde tespit edecektir.

28. SaaG-DAD, sistem yazılım birimleri arasındaki döngüsel bağımlılıkları Çekirdek Sistem Modeli üzerinde tespit edecektir.

29. SaaG-DAD, Çekirdek Sistem Modeli dahilindeki düğümler arasındaki kopuk, eksik, geçersiz veya karşılığı bulunmayan yapısal ilişkileri Çekirdek Sistem Modeli üzerinde tespit edecektir.

30. SaaG-DAD, detayları kritik tasarım aşamasında belirlenecek mimari kurallara aykırı tasarım örüntülerini Çekirdek Sistem Modeli üzerinde tespit edecektir.

31. SaaG-DAD, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisi kullanılarak analizler gerçekleştirebilecektir.

32. SaaG-DAD, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak düğümler arasındaki mesaj akış yönünü, mesaj sayısını, veri hacmini ve mesajlaşma sıklığını analiz edecektir.

33. SaaG-DAD, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak bir düğümün ya da ilişkinin devre dışı kalması durumunun Çekirdek Sistem Modeli üzerindeki etkilerini değerlendirebilecektir.

34. SaaG-DAD, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak tasarım zamanı trafik analizi yapabilecek ve simülasyon kapsamında oluşturulan yük koşullarının sistem varlıkları ve ilişkiler üzerindeki etkileri kapsamında en az aşağıdaki durumları değerlendirebilecektir:
    1. Topic/Mesaj yoğunluğunun artması,
    2. Topic/Mesaj yayın veya tüketim davranışının değişmesi.

35. SaaG-DAD, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak simülasyon kapsamında oluşturulan arıza, yük, iletişim kesintisi veya bant genişliği daralması durumlarının bağımlı düğümler üzerindeki yayılımını belirleyecek; doğrudan veya dolaylı olarak etkilenen düğümler/ilişkileri ve etkinin izlediği yayılım yolunu tespit edecektir.

36. SaaG-DAD, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak yapılacak simülasyon sonucunda en yüksek kaynak kullanımına sahip veya en yoğun mesajlaşan sistem varlıklarını belirleyecek ve özet değerlendirme göstergeleri olarak kullanıcıya sunacaktır.

37. SaaG-DAD, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisi kullanılarak analizler gerçekleştirebilecektir.

38. SaaG-DAD, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde en az aşağıdaki konular özelinde analizler gerçekleştirebilecektir:
    1. Çalışma ve sağlık durumları,
    2. İşlemci, bellek, depolama ve ağ kullanım değerleri,
    3. Hata, uyarı, yeniden başlatma ve zaman aşımı bilgileri,
    4. Mesaj akış yönü, mesaj sayısı, veri hacmi ve mesajlaşma sıklığı,
    5. İletişim gecikmesi, mesaj kaybı ve başarılı iletim oranları,
    6. Topic yayın ve tüketim etkinlikleri.

39. SaaG-DAD, Model Kurulum Verisindeki düğümler ve ilişkiler ile Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma zamanı sistem varlıklarını ve ilişkilerini karşılaştıracak ve en az aşağıdaki durumları tespit edecektir:
    1. Model Kurulum Verisinde yer aldığı hâlde çalışma zamanı verilerinde gözlemlenmeyen sistem varlıkları ve ilişkiler,
    2. Model Kurulum Verisinde yer almadığı hâlde çalışma zamanı verilerinde gözlemlenen sistem varlıkları ve ilişkiler,
    3. Model Kurulum Verisi ile çalışma zamanı verileri arasında uyumsuzluk bulunan sistem varlıkları ve ilişkiler.

40. SaaG-DAD, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde bulunan düğümler ve ilişkilerle bağlantılı olay kayıtlarını analiz edecektir.

41. SaaG-DAD, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak analiz sonucunda en yüksek kaynak kullanımına sahip veya en yoğun mesajlaşan sistem varlıklarını belirleyecek ve özet değerlendirme göstergeleri olarak kullanıcıya sunacaktır.

42. SaaG-DAD, tasarım doğrulama ve analiz sonuçlarını detayları kritik tasarım aşamasında belirlenecek kurallara/metriklere göre "uygun" veya "uygun değil" durumlarından biriyle sınıflandıracaktır.

43. SaaG-DAD, kullanıcının düğüm-ilişki yapısı üzerinde sistem varlığı veya ilişki araması yapabilmesini; sonuçları tür, proje, platform, sistem sürümü veya yazılım birimi bilgilerine göre süzebilmesini ve görsel yakınlaştırma, uzaklaştırma, taşıma ve düğüm/ilişki seçme, öznitelik görüntüleme işlemlerini gerçekleştirebilmesini sağlayacaktır.

44. SaaG-DAD, analiz sonuçlarında tespit edilen her bulguyu en az aşağıdaki bilgilerle birlikte kullanıcıya sunacaktır:
    1. Bulgu kimliği,
    2. Bulgu türü,
    3. Bulgu açıklaması,
    4. Etkilenen sistem varlığı veya ilişki,
    5. İlgili doğrulama kuralı veya kabul ölçütü,
    6. Bulguyu destekleyen veri veya kanıt,
    7. Bulgunun bilgilendirme, düşük, orta, yüksek veya kritik seviyelerinden biriyle ifade edilen önem derecesi.

45. SaaG-DAD, aynı işlem kapsamında tespit edilen birbiriyle ilişkili bulgular arasındaki neden-sonuç ilişkisini kayıt altına alacak ve kullanıcıya gösterecektir.

46. SaaG-DAD, kullanıcının bulguları işlem türü, değerlendirme sonucu, bulgu türü, önem derecesi, proje, platform, sistem sürümü veya etkilenen düğümlere göre sıralayabilmesini ve süzebilmesini sağlayacaktır.

47. SaaG-DAD, tasarım doğrulama, analiz ve simülasyon işlemi sırasında oluşan hata nedenini, işlemin kesildiği aşamayı ve hata zamanını kayıt altına alacaktır.

48. SaaG-DAD, simülasyon işlemlerinde kullanılan senaryo adını, senaryo girdilerini, veri üretim zamanını ve ilişkili proje, platform ve sistem sürüm bilgilerini kaydedebilecektir.

49. SaaG-DAD, tasarım doğrulama, analiz ve simülasyon sonuçlarının özet veya ayrıntılı sistem raporunu detayları kritik tasarım aşamasında belirlenecek dışa aktarılabilir dosya biçiminde oluşturacak ve raporlarda en az aşağıdaki bilgilerin yer almasını sağlayacaktır:
    1. Proje bilgisi,
    2. Platform bilgisi,
    3. Sistem sürüm bilgisi,
    4. Kullanılan Çekirdek Sistem Modeli,
    5. Kullanılan Analitik Değerlendirme Verisi ve veri kaynağı,
    6. İşlem kimliği ve işlem türü,
    7. İşlem başlangıç ve bitiş zamanı,
    8. Değerlendirme sonucu,
    9. Tespit edilen bulgular,
    10. Etkilenen düğümler ve ilişkiler,
    11. Önem dereceleri,
    12. Bulgulara ilişkin ilave bilgiler.

50. SaaG-DAD, kullanıcı arayüzleri üzerinden yapılan analiz isteklerini Derleme Otomasyon Araçları (Build Automation Tool) ve Komut Satırı Arayüzü (CLI) üzerinden de kabul edecek; sisteme erişen kullanıcılar ile otomasyon istemcilerine (Jenkins vb.) devam eden işlemlerin durum bilgisini sunacak ve analiz işlemlerinin birbirinden bağımsız olarak eş zamanlı yürütülmesini sağlayacaktır.

51. SaaG-DAD, bir yazılım biriminin hedef ortama kurulum uygunluğunu en az aşağıdaki değerlendirme başlıkları altında analiz edecektir:
    1. Yapısal ve mimari uygunluk,
    2. Arayüz, topic ve haberleşme uygunluğu,
    3. Bağımlılık ve entegrasyon uygunluğu,
    4. Kaynak ve performans yeterliliği.

52. SaaG-DAD, kurulum uygunluk değerlendirmesinde kullanılan her kontrol kuralını kural kimliği, değerlendirme başlığı, önem derecesi, ağırlık değeri, kabul ölçütü ve bloke edici olma durumu ile tanımlayacak; kural sonuçlarına ait uygunluk kategorileri ve puanlama yöntemi detayları kritik tasarım aşamasında belirlenecek şekilde sınıflandıracak ve puanlayacaktır.

53. SaaG-DAD, kritik önem derecesine sahip bir bulgunun veya değerlendirme profilinde bloke edici olarak tanımlanmış bir kontrol kuralı ihlalinin tespit edilmesi durumunda genel uygunluk puanından bağımsız olarak hedef ortama kurulum sonucunu "uygun değil" olarak belirleyecek ve üretim dağıtım hattının devam etmesini engelleyecek karar bilgisini otomasyon istemcisine iletecektir.

54. SaaG-DAD, üretim dağıtım hattı kapsamında bir veya birden fazla yazılım birimi için başlatılan kurulum uygunluk değerlendirmelerini birbirinden bağımsız işlem kimlikleriyle yürütecek; her yazılım birimi için ayrı uygunluk puanı, skor sınıfı, bloke edici bulgular ve kurulum kararının yanı sıra toplu işlem sonucunu makine tarafından işlenebilir biçimde otomasyon istemcisine sunacaktır.
