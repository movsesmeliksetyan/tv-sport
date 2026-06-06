package ru.pimpletv.tv.acestream

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri

/** Ace Stream hand-off (PRD §5). */
object AceStream {

    // Known Ace Stream Media Center packages. The TV/Android build is `org.acestream.node`;
    // older mobile builds use org.acestream.media[.atv]. Detection below prefers intent
    // resolution, so this list is only a fallback (R5).
    private val PACKAGES = listOf(
        "org.acestream.node",
        "org.acestream.media.atv",
        "org.acestream.media",
    )

    private fun viewIntent(contentIdOrUri: String): Intent {
        val uri = if (contentIdOrUri.startsWith("acestream://")) {
            Uri.parse(contentIdOrUri)
        } else {
            Uri.parse("acestream://$contentIdOrUri")
        }
        return Intent(Intent.ACTION_VIEW, uri).apply { addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) }
    }

    /**
     * Installed if anything can handle an `acestream://` VIEW intent. Resolving the
     * intent (vs. checking package names) is robust to build/package differences —
     * requires the matching `<queries>` entry in the manifest on Android 11+.
     */
    fun isInstalled(context: Context): Boolean {
        val pm = context.packageManager
        val probe = viewIntent("0000000000000000000000000000000000000000")
        if (pm.resolveActivity(probe, 0) != null) return true
        return PACKAGES.any { pkg ->
            try {
                pm.getPackageInfo(pkg, 0); true
            } catch (e: Exception) {
                false
            }
        }
    }

    /**
     * Launch a content id (40-char hex) or a full acestream:// URI in Ace Stream.
     * @return true if an activity handled it, false if Ace Stream is missing.
     */
    fun launch(context: Context, contentIdOrUri: String): Boolean {
        return try {
            context.startActivity(viewIntent(contentIdOrUri))
            true
        } catch (e: ActivityNotFoundException) {
            false
        }
    }
}
