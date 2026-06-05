package ru.pimpletv.tv.ui

import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.leanback.widget.ImageCardView
import androidx.leanback.widget.Presenter
import com.bumptech.glide.Glide
import ru.pimpletv.tv.R
import ru.pimpletv.tv.data.MatchSummary

/** Renders a match as a Leanback ImageCardView with a LIVE badge (FR-2, FR-4). */
class MatchCardPresenter : Presenter() {

    override fun onCreateViewHolder(parent: ViewGroup): ViewHolder {
        val card = ImageCardView(parent.context).apply {
            isFocusable = true
            isFocusableInTouchMode = true
            setMainImageDimensions(CARD_WIDTH, CARD_HEIGHT)
        }
        return ViewHolder(card)
    }

    override fun onBindViewHolder(viewHolder: ViewHolder, item: Any) {
        val match = item as MatchSummary
        val card = viewHolder.view as ImageCardView
        card.titleText = "${match.home.name} – ${match.away.name}"
        val time = match.kickoff.substringAfter('T').take(5)
        card.contentText = buildString {
            append(time)
            match.tournament?.let { append("  •  ").append(it) }
            if (match.hasStream) append("   ● ").append(card.context.getString(R.string.badge_live))
        }
        card.mainImageView.setImageDrawable(
            ContextCompat.getDrawable(card.context, R.drawable.default_card)
        )
        val logo = match.home.logo
        if (!logo.isNullOrBlank()) {
            Glide.with(card.context)
                .load(logo)
                .placeholder(R.drawable.default_card)
                .into(card.mainImageView)
        }
    }

    override fun onUnbindViewHolder(viewHolder: ViewHolder) {
        (viewHolder.view as ImageCardView).mainImage = null
    }

    companion object {
        private const val CARD_WIDTH = 320
        private const val CARD_HEIGHT = 220
    }
}
