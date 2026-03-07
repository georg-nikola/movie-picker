package com.georgnikola.moviepicker.ui.watched

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.georgnikola.moviepicker.data.MoviesRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class WatchedUiState(
    val watchedMovies: List<String> = emptyList()
)

class WatchedViewModel(private val repository: MoviesRepository) : ViewModel() {

    val uiState: StateFlow<WatchedUiState> = repository.watchedMovies
        .map { set -> WatchedUiState(watchedMovies = set.sorted()) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = WatchedUiState()
        )

    fun removeWatched(title: String) {
        viewModelScope.launch { repository.removeWatched(title) }
    }
}

class WatchedViewModelFactory(private val repository: MoviesRepository) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T = WatchedViewModel(repository) as T
}
