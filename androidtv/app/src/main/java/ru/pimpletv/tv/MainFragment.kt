package ru.pimpletv.tv

import android.os.Bundle
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.leanback.app.BrowseSupportFragment
import androidx.leanback.widget.ArrayObjectAdapter
import androidx.leanback.widget.HeaderItem
import androidx.leanback.widget.ListRow
import androidx.leanback.widget.ListRowPresenter
import kotlinx.coroutines.launch
import ru.pimpletv.tv.data.MatchRepository
import ru.pimpletv.tv.data.MatchSummary
import ru.pimpletv.tv.ui.MatchCardPresenter

/**
 * Browse skeleton (PRD §8 step 2). Phase 3 (T3.2–T3.4) expands rows, detail
 * navigation, and polling. For now it fetches once and groups by sport so the
 * Leanback + Retrofit + Glide + coroutines stack is exercised end-to-end.
 */
class MainFragment : BrowseSupportFragment() {

    private val repository = MatchRepository()
    private val rowsAdapter = ArrayObjectAdapter(ListRowPresenter())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = getString(R.string.browse_title)
        headersState = HEADERS_ENABLED
        isHeadersTransitionOnBackEnabled = true
        brandColor = ContextCompat.getColor(requireContext(), R.color.brand_primary)
        adapter = rowsAdapter
        loadMatches()
    }

    private fun loadMatches() {
        viewLifecycleOwnerLiveData.value // ensure view exists; safe no-op
        lifecycleScope.launch {
            runCatching { repository.matches() }
                .onSuccess { populate(it) }
                .onFailure {
                    Toast.makeText(requireContext(), R.string.error_load, Toast.LENGTH_LONG).show()
                }
        }
    }

    private fun populate(matches: List<MatchSummary>) {
        rowsAdapter.clear()
        val cardPresenter = MatchCardPresenter()

        val live = matches.filter { it.hasStream || it.status == "live" }
        addRow(getString(R.string.row_live), live, cardPresenter)
        addRow(getString(R.string.row_football), matches.filter { it.sport == "football" }, cardPresenter)
        addRow(getString(R.string.row_hockey), matches.filter { it.sport == "hockey" }, cardPresenter)
    }

    private fun addRow(title: String, items: List<MatchSummary>, presenter: MatchCardPresenter) {
        if (items.isEmpty()) return
        val listRowAdapter = ArrayObjectAdapter(presenter).apply { items.forEach { add(it) } }
        rowsAdapter.add(ListRow(HeaderItem(title), listRowAdapter))
    }
}
