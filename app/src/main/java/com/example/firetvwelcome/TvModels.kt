package com.example.firetvwelcome

data class WelcomePayload(
    val property: PropertyPayload,
    val stay: StayPayload,
    val refreshSeconds: Int
)

data class PropertyPayload(
    val id: String,
    val name: String,
    val address: String,
    val wifiName: String,
    val wifiPassword: String,
    val checkInNote: String,
    val checkoutNote: String,
    val houseTips: List<String>,
    val contactName: String,
    val contactPhone: String
)

data class StayPayload(
    val guestName: String,
    val guestCount: Int,
    val arrivalDate: String,
    val departureDate: String,
    val occasion: String,
    val message: String
)

data class DevicePayload(
    val id: String,
    val name: String,
    val pairingCode: String,
    val propertyId: String,
    val status: String
)

data class RegisterDevicePayload(
    val device: DevicePayload,
    val message: String
)
