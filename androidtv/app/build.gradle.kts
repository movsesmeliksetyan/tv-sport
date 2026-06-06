plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "ru.pimpletv.tv"
    compileSdk = 35

    defaultConfig {
        applicationId = "ru.pimpletv.tv"
        minSdk = 21              // Android TV baseline (PRD §3.2)
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        // Production default: the Raspberry Pi backend, via the Pi-hole local DNS name.
        // A real TV on the LAN (using Pi-hole for DNS) resolves pimpletv.pi -> the Pi.
        buildConfigField("String", "API_BASE_URL", "\"http://pimpletv.pi:8090/\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
        debug {
            // Emulator can't resolve the .pi domain (it doesn't use Pi-hole), so hit the Pi's IP directly.
            buildConfigField("String", "API_BASE_URL", "\"http://192.168.0.57:8090/\"")
        }
    }

    buildFeatures {
        buildConfig = true
        compose = true
    }

    compileOptions {
        isCoreLibraryDesugaringEnabled = true  // java.time on minSdk 21
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.foundation)
    implementation(libs.androidx.compose.material.icons)
    implementation(libs.androidx.compose.ui.tooling.preview)
    debugImplementation(libs.androidx.compose.ui.tooling)
    implementation(libs.androidx.tv.material)

    implementation(libs.coil.compose)
    coreLibraryDesugaring(libs.desugar.jdk.libs)

    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.gson)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.coroutines.android)
}
