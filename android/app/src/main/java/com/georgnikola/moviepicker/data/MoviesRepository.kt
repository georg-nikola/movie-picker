package com.georgnikola.moviepicker.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringSetPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "movie_prefs")

class MoviesRepository(private val context: Context) {

    private object Keys {
        val WATCHED_MOVIES = stringSetPreferencesKey("watched_movies")
        val SKIP_WATCHED = booleanPreferencesKey("skip_watched")
    }

    val watchedMovies: Flow<Set<String>> = context.dataStore.data.map { prefs ->
        prefs[Keys.WATCHED_MOVIES] ?: emptySet()
    }

    val skipWatched: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[Keys.SKIP_WATCHED] ?: false
    }

    fun pickRandom(currentWatched: Set<String>, skip: Boolean): PickedMovie {
        val pool = if (skip && currentWatched.isNotEmpty())
            Movies.titles.filterNot { it in currentWatched }
        else
            Movies.titles

        val effective = if (pool.isEmpty()) Movies.titles else pool
        val title = effective.random()
        return PickedMovie(title = title, index = Movies.titles.indexOf(title) + 1)
    }

    suspend fun addWatched(title: String) {
        context.dataStore.edit { prefs ->
            val current = prefs[Keys.WATCHED_MOVIES] ?: emptySet()
            prefs[Keys.WATCHED_MOVIES] = current + title
        }
    }

    suspend fun removeWatched(title: String) {
        context.dataStore.edit { prefs ->
            val current = prefs[Keys.WATCHED_MOVIES] ?: emptySet()
            prefs[Keys.WATCHED_MOVIES] = current - title
        }
    }

    suspend fun setSkipWatched(skip: Boolean) {
        context.dataStore.edit { prefs ->
            prefs[Keys.SKIP_WATCHED] = skip
        }
    }
}

data class PickedMovie(val title: String, val index: Int)
