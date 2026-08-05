package com.vidroidcall.elderly

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.text.Normalizer
import java.util.Locale

/**
 * Mockup "trợ lý giọng nói cho người lớn tuổi" — minh hoạ UX xác nhận lệnh
 * bằng giọng nói, dùng SpeechRecognizer/TextToSpeech thật của Android. Đây
 * là bản trình diễn UX, KHÔNG gọi điện/nhắn tin thật (đúng nguyên tắc an
 * toàn của bộ nền ViDroidCall Studio).
 */
class MainActivity : AppCompatActivity(), RecognitionListener {

    private val handler = Handler(Looper.getMainLooper())
    private var speechRecognizer: SpeechRecognizer? = null
    private lateinit var recognizerIntent: Intent
    private lateinit var tts: TextToSpeech

    private lateinit var riskTag: TextView
    private lateinit var states: Map<String, View>

    private lateinit var tvListeningStatus: TextView
    private lateinit var tvAutoText: TextView
    private lateinit var tvConfirmText: TextView
    private lateinit var tvExecutingText: TextView
    private lateinit var tvDoneText: TextView
    private lateinit var tvClarifyText: TextView

    private var pendingConfirmAction: (() -> Unit)? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        riskTag = findViewById(R.id.tvRiskTag)
        states = mapOf(
            "home" to findViewById(R.id.stateHome),
            "listening" to findViewById(R.id.stateListening),
            "permission" to findViewById(R.id.statePermission),
            "auto" to findViewById(R.id.stateAuto),
            "confirm" to findViewById(R.id.stateConfirm),
            "executing" to findViewById(R.id.stateExecuting),
            "done" to findViewById(R.id.stateDone),
            "cancelled" to findViewById(R.id.stateCancelled),
            "clarify" to findViewById(R.id.stateClarify),
            "not_understood" to findViewById(R.id.stateNotUnderstood),
        )

        tvListeningStatus = findViewById(R.id.tvListeningStatus)
        tvAutoText = findViewById(R.id.tvAutoText)
        tvConfirmText = findViewById(R.id.tvConfirmText)
        tvExecutingText = findViewById(R.id.tvExecutingText)
        tvDoneText = findViewById(R.id.tvDoneText)
        tvClarifyText = findViewById(R.id.tvClarifyText)

        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts.language = Locale("vi", "VN")
            }
        }

        recognizerIntent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "vi-VN")
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }

        findViewById<View>(R.id.btnMic).setOnClickListener { onMicTapped() }
        findViewById<Button>(R.id.btnGrantPermission).setOnClickListener { requestMicPermission() }
        findViewById<Button>(R.id.btnConfirmYes).setOnClickListener { onConfirmYes() }
        findViewById<Button>(R.id.btnConfirmNo).setOnClickListener { onConfirmNo() }
        findViewById<Button>(R.id.btnDoneHome).setOnClickListener { showHome() }
        findViewById<Button>(R.id.btnCancelledHome).setOnClickListener { showHome() }
        findViewById<Button>(R.id.btnClarifyRetry).setOnClickListener { onMicTapped() }
        findViewById<Button>(R.id.btnNotUnderstoodRetry).setOnClickListener { onMicTapped() }

        showHome()
    }

    // --- Trạng thái màn hình ---

    private fun showOnly(name: String) {
        states.forEach { (key, view) -> view.visibility = if (key == name) View.VISIBLE else View.GONE }
    }

    private fun showHome() {
        riskTag.visibility = View.GONE
        showOnly("home")
    }

    private fun showListening() {
        riskTag.visibility = View.GONE
        tvListeningStatus.text = getString(R.string.listening)
        showOnly("listening")
    }

    private fun showPermissionRequest(deniedBefore: Boolean) {
        findViewById<TextView>(R.id.tvPermissionText).setText(
            if (deniedBefore) R.string.permission_denied else R.string.permission_needed
        )
        showOnly("permission")
    }

    private fun showAuto(text: String, risk: String) {
        riskTag.text = risk
        riskTag.visibility = View.VISIBLE
        tvAutoText.text = text
        showOnly("auto")
    }

    private fun showConfirm(text: String, risk: String, onYes: () -> Unit) {
        riskTag.text = risk
        riskTag.visibility = View.VISIBLE
        tvConfirmText.text = text
        pendingConfirmAction = onYes
        showOnly("confirm")
    }

    private fun showExecuting(text: String) {
        tvExecutingText.text = text
        showOnly("executing")
    }

    private fun showDone(text: String) {
        tvDoneText.text = text
        showOnly("done")
    }

    private fun showCancelled() {
        showOnly("cancelled")
    }

    private fun showClarify(text: String, risk: String) {
        riskTag.text = risk
        riskTag.visibility = View.VISIBLE
        tvClarifyText.text = text
        showOnly("clarify")
    }

    private fun showNotUnderstood() {
        riskTag.visibility = View.GONE
        showOnly("not_understood")
    }

    // --- Quyền micro ---

    private fun hasMicPermission() =
        ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED

    private fun requestMicPermission() {
        ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), REQUEST_MIC)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_MIC) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                onMicTapped()
            } else {
                showPermissionRequest(deniedBefore = true)
            }
        }
    }

    // --- Nhận diện giọng nói ---

    private fun onMicTapped() {
        if (!hasMicPermission()) {
            showPermissionRequest(deniedBefore = false)
            return
        }
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            Toast.makeText(
                this,
                "Máy này chưa hỗ trợ nhận diện giọng nói (cần Google app). Hãy thử trên điện thoại thật có cài Google.",
                Toast.LENGTH_LONG
            ).show()
            return
        }
        showListening()
        speechRecognizer?.destroy()
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this).also {
            it.setRecognitionListener(this)
            it.startListening(recognizerIntent)
        }
    }

    private fun speak(text: String) {
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "vidroidcall_utterance")
    }

    private fun handleRecognized(rawText: String) {
        val text = normalize(rawText)
        when {
            text.contains("bao thuc") || text.contains("hen gio") || text.contains("dat gio") -> {
                val reply = "Đã đặt báo thức 6:00 sáng mai"
                speak(reply)
                showAuto(reply, "risk_level: low")
                handler.postDelayed({ showHome() }, 2200)
            }
            text.contains("goi") -> {
                val reply = "Bác muốn gọi cho Con trai, đúng không ạ?"
                speak(reply)
                showConfirm(reply, "risk_level: high — cần xác nhận") {
                    val executing = "Đang gọi Con trai..."
                    showExecuting(executing)
                    speak("Đang gọi Con trai")
                    handler.postDelayed({
                        showDone("Đã gọi xong")
                        speak("Đã gọi xong")
                    }, 1200)
                }
            }
            text.contains("nhan") -> {
                val reply = "Bác muốn nhắn nội dung gì cho Nam ạ?"
                speak(reply)
                showClarify(reply, "intent: clarify — thiếu nội dung tin nhắn")
            }
            else -> {
                speak("Bác vui lòng nói lại")
                showNotUnderstood()
            }
        }
    }

    private fun onConfirmYes() {
        pendingConfirmAction?.invoke()
    }

    private fun onConfirmNo() {
        speak("Đã huỷ")
        showCancelled()
    }

    private fun normalize(input: String): String {
        val lower = input.lowercase(Locale("vi", "VN")).replace('đ', 'd')
        val decomposed = Normalizer.normalize(lower, Normalizer.Form.NFD)
        return decomposed.replace(Regex("\\p{Mn}+"), "")
    }

    // --- RecognitionListener ---

    override fun onReadyForSpeech(params: Bundle?) {}

    override fun onBeginningOfSpeech() {}

    override fun onRmsChanged(rmsdB: Float) {}

    override fun onBufferReceived(buffer: ByteArray?) {}

    override fun onEndOfSpeech() {
        tvListeningStatus.text = getString(R.string.thinking)
    }

    override fun onError(error: Int) {
        showNotUnderstood()
    }

    override fun onResults(results: Bundle?) {
        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        val best = matches?.firstOrNull().orEmpty()
        if (best.isBlank()) {
            showNotUnderstood()
        } else {
            handleRecognized(best)
        }
    }

    override fun onPartialResults(partialResults: Bundle?) {
        val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        val best = matches?.firstOrNull()
        if (!best.isNullOrBlank() && states["listening"]?.visibility == View.VISIBLE) {
            tvListeningStatus.text = "“$best”"
        }
    }

    override fun onEvent(eventType: Int, params: Bundle?) {}

    override fun onDestroy() {
        speechRecognizer?.destroy()
        tts.stop()
        tts.shutdown()
        super.onDestroy()
    }

    companion object {
        private const val REQUEST_MIC = 101
    }
}
