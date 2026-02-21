import enum


class StudyForm(str, enum.Enum):
    full_time = "full_time"      # очная
    part_time = "part_time"      # заочная/вечерняя


class Language(str, enum.Enum):
    ru = "russian"
    kg = "kyrgyz"
    en = "english"
    tr = "turkish"


class UserRole(str, enum.Enum):
    applicant = "applicant"
    admin = "admin"
    superadmin = "superadmin"


class Currency(str, enum.Enum):
    KGS = "KGS"
    USD = "USD"
    EUR = "EUR"


class DocumentType(str, enum.Enum):
    admission_rules = "admission_rules"
    fee_table = "fee_table"
    deadlines = "deadlines"
    other = "other"


class TagType(str, enum.Enum):
    interest = "interest"     # интересы пользователя / тематики программ
    strength = "strength"     # сильные стороны
    subject = "subject"       # предметы (математика, биология...)
    career = "career"         # карьера (backend, doctor...)


class City(str, enum.Enum):
    """Города Кыргызстана."""
    bishkek = "bishkek"
    osh = "osh"
    jalal_abad = "jalal_abad"
    karakol = "karakol"
    tokmok = "tokmok"
    naryn = "naryn"
    batken = "batken"
    talas = "talas"
    uzgen = "uzgen"
    kara_balta = "kara_balta"
    balykchy = "balykchy"
    bazar_korgon = "bazar_korgon"
    kyzyl_kiya = "kyzyl_kiya"
    tash_kumyr = "tash_kumyr"
    kant = "kant"
    isfana = "isfana"
    mailuu_suu = "mailuu_suu"
    kara_suu = "kara_suu"
    other = "other"  # другой город