package com.example.firetvwelcome

import android.os.Bundle
import android.provider.Settings
import android.view.KeyEvent
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    private lateinit var repository: TvRepository
    private lateinit var preferencesStore: PreferencesStore

    private lateinit var setupPanel: View
    private lateinit var pairingPanel: View
    private lateinit var contentPanel: View
    private lateinit var progressBar: ProgressBar
    private lateinit var errorText: TextView

    private lateinit var serverUrlInput: EditText
    private lateinit var saveConfigButton: Button
    private lateinit var restartPairingButton: Button
    private lateinit var editConfigButton: Button
    private lateinit var retryButton: Button

    private lateinit var pairingCodeText: TextView
    private lateinit var pairingDeviceNameText: TextView
    private lateinit var pairingStatusText: TextView

    private lateinit var greetingText: TextView
    private lateinit var propertyText: TextView
    private lateinit var stayText: TextView
    private lateinit var guestCountText: TextView
    private lateinit var occasionText: TextView
    private lateinit var messageText: TextView
    private lateinit var wifiNameText: TextView
    private lateinit var wifiPasswordText: TextView
    private lateinit var hostNameText: TextView
    private lateinit var hostPhoneText: TextView
    private lateinit var checkInText: TextView
    private lateinit var checkoutText: TextView
    private lateinit var tipsText: TextView

    private var refreshJob: Job? = null
    private var pendingDevice: DevicePayload? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        repository = TvRepository()
        preferencesStore = PreferencesStore(this)

        bindViews()
        bindActions()
        populateSavedConfig()
        showCorrectState()
    }

    override fun onResume() {
        super.onResume()
        when {
            !preferencesStore.hasServerUrl() -> showSetup()
            preferencesStore.deviceId().isBlank() -> registerCurrentDevice()
            else -> loadWelcomeLoop()
        }
    }

    override fun onPause() {
        super.onPause()
        refreshJob?.cancel()
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_MENU) {
            showSetup()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    private fun bindViews() {
        setupPanel = findViewById(R.id.setupPanel)
        pairingPanel = findViewById(R.id.pairingPanel)
        contentPanel = findViewById(R.id.contentPanel)
        progressBar = findViewById(R.id.progressBar)
        errorText = findViewById(R.id.errorText)

        serverUrlInput = findViewById(R.id.serverUrlInput)
        saveConfigButton = findViewById(R.id.saveConfigButton)
        restartPairingButton = findViewById(R.id.restartPairingButton)
        editConfigButton = findViewById(R.id.editConfigButton)
        retryButton = findViewById(R.id.retryButton)

        pairingCodeText = findViewById(R.id.pairingCodeText)
        pairingDeviceNameText = findViewById(R.id.pairingDeviceNameText)
        pairingStatusText = findViewById(R.id.pairingStatusText)

        greetingText = findViewById(R.id.greetingText)
        propertyText = findViewById(R.id.propertyText)
        stayText = findViewById(R.id.stayText)
        guestCountText = findViewById(R.id.guestCountText)
        occasionText = findViewById(R.id.occasionText)
        messageText = findViewById(R.id.messageText)
        wifiNameText = findViewById(R.id.wifiNameText)
        wifiPasswordText = findViewById(R.id.wifiPasswordText)
        hostNameText = findViewById(R.id.hostNameText)
        hostPhoneText = findViewById(R.id.hostPhoneText)
        checkInText = findViewById(R.id.checkInText)
        checkoutText = findViewById(R.id.checkoutText)
        tipsText = findViewById(R.id.tipsText)
    }

    private fun bindActions() {
        saveConfigButton.setOnClickListener {
            val serverUrl = serverUrlInput.text.toString().trim()
            if (serverUrl.isBlank()) {
                errorText.visibility = View.VISIBLE
                errorText.text = getString(R.string.server_only_validation_error)
                return@setOnClickListener
            }

            preferencesStore.saveServerUrl(serverUrl)
            preferencesStore.clearDeviceId()
            registerCurrentDevice()
        }

        restartPairingButton.setOnClickListener {
            preferencesStore.clearDeviceId()
            registerCurrentDevice()
        }

        editConfigButton.setOnClickListener { showSetup() }
        retryButton.setOnClickListener {
            if (preferencesStore.deviceId().isBlank()) {
                registerCurrentDevice()
            } else {
                loadWelcomeLoop()
            }
        }
    }

    private fun populateSavedConfig() {
        serverUrlInput.setText(preferencesStore.serverUrl())
    }

    private fun showCorrectState() {
        when {
            !preferencesStore.hasServerUrl() -> showSetup()
            preferencesStore.deviceId().isBlank() -> showPairing(null)
            else -> showContent()
        }
    }

    private fun showSetup() {
        refreshJob?.cancel()
        setupPanel.visibility = View.VISIBLE
        pairingPanel.visibility = View.GONE
        contentPanel.visibility = View.GONE
        progressBar.visibility = View.GONE
        errorText.visibility = View.GONE
        saveConfigButton.requestFocus()
    }

    private fun showPairing(device: DevicePayload?) {
        setupPanel.visibility = View.GONE
        pairingPanel.visibility = View.VISIBLE
        contentPanel.visibility = View.GONE
        progressBar.visibility = View.GONE
        pendingDevice = device
        pairingCodeText.text = device?.pairingCode ?: "--"
        pairingDeviceNameText.text = device?.name ?: getString(R.string.default_tv_name)
        pairingStatusText.text = if (device == null) {
            getString(R.string.pairing_waiting_copy)
        } else {
            getString(R.string.pairing_copy, device.pairingCode)
        }
        restartPairingButton.requestFocus()
    }

    private fun showContent() {
        setupPanel.visibility = View.GONE
        pairingPanel.visibility = View.GONE
        contentPanel.visibility = View.VISIBLE
    }

    private fun registerCurrentDevice() {
        refreshJob?.cancel()
        showPairing(null)
        progressBar.visibility = View.VISIBLE
        errorText.visibility = View.GONE

        refreshJob = lifecycleScope.launch {
            val deviceName = buildDeviceName()
            val existingId = preferencesStore.deviceId()
            val result = repository.registerDevice(
                baseUrl = preferencesStore.serverUrl(),
                deviceId = existingId,
                deviceName = deviceName
            )

            progressBar.visibility = View.GONE

            result.onSuccess { payload ->
                preferencesStore.saveDeviceId(payload.device.id)
                showPairing(payload.device)
                pollUntilPaired()
            }.onFailure { error ->
                errorText.visibility = View.VISIBLE
                errorText.text = error.message ?: getString(R.string.load_failed)
            }
        }
    }

    private fun pollUntilPaired() {
        refreshJob?.cancel()
        refreshJob = lifecycleScope.launch {
            while (true) {
                val result = repository.fetchWelcome(
                    baseUrl = preferencesStore.serverUrl(),
                    deviceId = preferencesStore.deviceId()
                )

                if (result.isSuccess) {
                    showContent()
                    renderWelcome(result.getOrThrow())
                    loadWelcomeLoop()
                    return@launch
                }

                showPairing(pendingDevice)
                errorText.visibility = View.GONE
                delay(5000)
            }
        }
    }

    private fun loadWelcomeLoop() {
        refreshJob?.cancel()
        refreshJob = lifecycleScope.launch {
            while (true) {
                val refreshSeconds = fetchAndRenderOnce()
                delay(refreshSeconds * 1000L)
            }
        }
    }

    private suspend fun fetchAndRenderOnce(): Int {
        progressBar.visibility = View.VISIBLE
        errorText.visibility = View.GONE

        val result = repository.fetchWelcome(
            baseUrl = preferencesStore.serverUrl(),
            deviceId = preferencesStore.deviceId()
        )

        progressBar.visibility = View.GONE

        if (result.isSuccess) {
            val payload = result.getOrThrow()
            showContent()
            renderWelcome(payload)
            return payload.refreshSeconds
        }

        val message = result.exceptionOrNull()?.message.orEmpty()
        if (message.contains("not paired", ignoreCase = true)) {
            showPairing(pendingDevice)
            pollUntilPaired()
        } else {
            errorText.visibility = View.VISIBLE
            errorText.text = if (message.isBlank()) getString(R.string.load_failed) else message
        }

        return 300
    }

    private fun renderWelcome(payload: WelcomePayload) {
        greetingText.text = getString(R.string.greeting_format, payload.stay.guestName)
        propertyText.text = "${payload.property.name} - ${payload.property.address}"
        stayText.text = "${payload.stay.arrivalDate} - ${payload.stay.departureDate}"
        guestCountText.text = resources.getQuantityString(
            R.plurals.guest_count,
            payload.stay.guestCount,
            payload.stay.guestCount
        )
        occasionText.text = payload.stay.occasion.ifBlank { getString(R.string.default_occasion) }
        messageText.text = payload.stay.message.ifBlank { getString(R.string.default_message) }
        wifiNameText.text = payload.property.wifiName
        wifiPasswordText.text = payload.property.wifiPassword
        hostNameText.text = payload.property.contactName
        hostPhoneText.text = payload.property.contactPhone
        checkInText.text = payload.property.checkInNote
        checkoutText.text = payload.property.checkoutNote
        tipsText.text = if (payload.property.houseTips.isEmpty()) {
            getString(R.string.no_house_notes)
        } else {
            payload.property.houseTips.joinToString(separator = "\n- ", prefix = "- ")
        }
    }

    private fun buildDeviceName(): String {
        val androidId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID).takeLast(4)
        return "Fire TV $androidId"
    }
}
