# DataStore
-keepclassmembers class * extends androidx.datastore.preferences.protobuf.GeneratedMessageLite {
    <fields>;
}

# Kotlin serialization (keep data class fields)
-keepattributes *Annotation*, InnerClasses
-keepclassmembers class com.georgnikola.moviepicker.** { *; }

# Compose tooling not needed in release
-dontwarn androidx.compose.ui.tooling.**
