package com.georgnikola.moviepicker.ui.browser

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.georgnikola.moviepicker.data.Movies
import com.georgnikola.moviepicker.data.MoviesRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

enum class SortOrder { BY_INDEX, ALPHABETICAL }

data class MovieEntry(
    val title: String,
    val index: Int,       // 1-based position in the curated list
    val isWatched: Boolean
)

data class BrowserUiState(
    val query: String = "",
    val sortOrder: SortOrder = SortOrder.BY_INDEX,
    val allEntries: List<MovieEntry> = emptyList(),
    val watchedCount: Int = 0,
) {
    val filtered: List<MovieEntry>
        get() {
            val q = query.trim().lowercase()
            val source = if (q.isEmpty()) allEntries
                         else allEntries.filter { it.title.lowercase().contains(q) }
            return when (sortOrder) {
                SortOrder.BY_INDEX   -> source
                SortOrder.ALPHABETICAL -> source.sortedBy { it.title.lowercase() }
            }
        }
}

class MovieBrowserViewModel(private val repository: MoviesRepository) : ViewModel() {

    private val _query = MutableStateFlow("")
    private val _sortOrder = MutableStateFlow(SortOrder.BY_INDEX)

    val uiState: StateFlow<BrowserUiState> = combine(
        repository.watchedMovies,
        _query,
        _sortOrder
    ) { watched, query, sortOrder ->
        val entries = Movies.titles.mapIndexed { i, title ->
            MovieEntry(title = title, index = i + 1, isWatched = title in watched)
        }
        BrowserUiState(
            query = query,
            sortOrder = sortOrder,
            allEntries = entries,
            watchedCount = watched.size
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = BrowserUiState()
    )

    fun setQuery(q: String) = _query.update { q }

    fun setSortOrder(order: SortOrder) = _sortOrder.update { order }

    fun toggleWatched(entry: MovieEntry) {
        viewModelScope.launch {
            if (entry.isWatched) repository.removeWatched(entry.title)
            else repository.addWatched(entry.title)
        }
    }
}

class MovieBrowserViewModelFactory(
    private val repository: MoviesRepository
) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T =
        MovieBrowserViewModel(repository) as T
}
