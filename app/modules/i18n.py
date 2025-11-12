
import streamlit as st
LANGS = {
 'id': {
   'home_preflight': 'Laporan Preflight',
   'wizard': 'Data Wizard',
   'suppliers': 'Pemasok',
   'supplier_profile': 'Profil Pemasok',
   'labs': 'Lab (What-If & Skenario)',
   'optimizer_allocation': 'Optimizer & Alokasi',
   'export': 'Ekspor',
   'apply_save': 'Simpan Perubahan',
   'reset': 'Reset',
 },
 'en': {
   'home_preflight': 'Preflight Report',
   'wizard': 'Data Wizard',
   'suppliers': 'Suppliers',
   'supplier_profile': 'Supplier Profile',
   'labs': 'Labs (What-If & Scenarios)',
   'optimizer_allocation': 'Optimizer & Allocation',
   'export': 'Export',
   'apply_save': 'Save Changes',
   'reset': 'Reset',
 }
}
def t(key, lang='id'):
    return LANGS.get(lang, LANGS['id']).get(key, key)
