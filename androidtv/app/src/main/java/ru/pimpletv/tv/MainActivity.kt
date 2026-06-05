package ru.pimpletv.tv

import android.os.Bundle
import androidx.fragment.app.FragmentActivity

/** Single-activity host for the Leanback browse fragment. */
class MainActivity : FragmentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
    }
}
