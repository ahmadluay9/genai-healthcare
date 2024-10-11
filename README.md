# Dokumentasi API `/get_summarize_gemini`

## Endpoint: `/get_summarize_gemini`

**Metode:** `POST`

**Deskripsi:** Endpoint ini menerima file audio MP3 dan menghasilkan ringkasan percakapan dalam audio tersebut, memberikan kemungkinan diagnosis, dan rekomendasi obat.  Ringkasan, diagnosis, dan rekomendasi obat diberikan dalam bahasa Indonesia.

**Header:**

* `X-API-Key`:  API key yang valid diperlukan untuk autentikasi.

**Body (form-data):**

* `file`: File audio MP3 yang akan diringkas.
* `model_name` (opsional): Nama model Gemini yang akan digunakan. Defaultnya adalah `gemini-1.5-pro-001`.

**Response (jika berhasil):**
json
{
"content": "## Ringkasan Gejala:\n Gejala 1\n Gejala 2\n Gejala 3\n\n## Diagnosis:\nDiagnosis\n\n## Rekomendasi Obat:\n[Gejala atau Diagnosis]:\n- Obat 1\n- Obat 2\n- Obat 3"
}


**Kode Status:**

* `200 OK`:  Berhasil. Response berisi ringkasan dalam format JSON seperti di atas.
* `400 Bad Request`:  Terjadi kesalahan, misalnya format file yang salah atau data yang tidak valid.  Response berisi pesan kesalahan.
* `401 Unauthorized`:  API key tidak valid atau hilang.
* `500 Internal Server Error`:  Terjadi kesalahan di server. Response berisi pesan kesalahan.


## Contoh Penggunaan

### Postman:

1. Buka Postman dan buat request baru dengan metode `POST`.
2. Masukkan URL endpoint: `http://localhost:8000/get_summarize_gemini` (ganti `localhost:8000` dengan alamat server Anda).
3. Di tab "Headers", tambahkan header `X-API-Key` dengan nilai API key Anda.
4. Di tab "Body", pilih "form-data".
5. Tambahkan key `file` dan pilih file MP3 Anda.
6. (Opsional) Tambahkan key `model_name` jika ingin menggunakan model yang berbeda.
7. Klik "Send".


### Curl:
bash
curl -X POST \
-H "X-API-Key: YOUR_API_KEY" \
-F "file=@/path/to/your/audio.mp3" \
-F "model_name=gemini-1.5-pro-001" \
http://localhost:8000/get_summarize_gemini


## Catatan:

* Pastikan Anda telah menginstal dependensi yang diperlukan dan menjalankan server FastAPI.
* API key harus disimpan dengan aman dan tidak boleh di-hardcode dalam kode atau request.
* Dokumentasi ini mengasumsikan server berjalan di `localhost:8000`.  Sesuaikan URL sesuai kebutuhan.