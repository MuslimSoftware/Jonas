import React from 'react';
import {
  StyleSheet,
  Pressable,
  Image,
  View,
  ActivityIndicator,
  Text,
} from 'react-native';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Theme } from '@/features/shared/context/ThemeContext';
import { ScreenshotControls } from '../common/ScreenshotControls'; // Adjusted import path
import { ScreenshotData } from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';
import { paddings } from '@/features/shared/theme/spacing';

interface BrowserTabProps {
  screenshots: ScreenshotData[];
  screenshotsError: ApiError | null;
  loadingScreenshots: boolean;
  totalScreenshotsCount: number | null;
  currentScreenshotIndex: number;
  loadingMoreScreenshots: boolean;
  hasMoreScreenshots: boolean;
  fetchMoreScreenshots: () => void;
  openImageModal: (uri: string) => void;
  setCurrentScreenshotIndex: React.Dispatch<React.SetStateAction<number>>;
  justLoadedMoreRef: React.MutableRefObject<boolean>;
}

export const BrowserTab: React.FC<BrowserTabProps> = ({
  screenshots,
  screenshotsError,
  loadingScreenshots,
  totalScreenshotsCount,
  currentScreenshotIndex,
  loadingMoreScreenshots,
  hasMoreScreenshots,
  fetchMoreScreenshots,
  openImageModal,
  setCurrentScreenshotIndex,
  justLoadedMoreRef,
}) => {
  const { theme } = useTheme();
  const styles = getStyles(theme);

  return (
    <View style={styles.tabContentContainer}>
      {screenshotsError ? (
        <Text style={styles.errorText}>Error loading screenshots.</Text>
      ) : totalScreenshotsCount !== null && totalScreenshotsCount > 0 ? (
        <View style={styles.carouselContainer}>
          <Pressable
            style={styles.screenshotImageWrapper}
            onPress={() =>
              screenshots[currentScreenshotIndex]?.image_data &&
              openImageModal(screenshots[currentScreenshotIndex].image_data)
            }
            disabled={!screenshots[currentScreenshotIndex]?.image_data}
          >
            {loadingMoreScreenshots || !screenshots[currentScreenshotIndex] ? (
              <View style={styles.screenshotImage}>
                <ActivityIndicator color={theme.colors.text.primary} />
              </View>
            ) : (
              <Image
                source={{ uri: screenshots[currentScreenshotIndex].image_data }}
                style={styles.screenshotImage}
                resizeMode="contain"
              />
            )}
          </Pressable>
          <ScreenshotControls
            currentIndex={currentScreenshotIndex}
            totalLoaded={screenshots.length}
            totalCount={totalScreenshotsCount}
            isLoadingMore={loadingMoreScreenshots}
            onGoBack={() => {
              // NOTE: Logic seems reversed (Back goes forward, Forward goes back)
              // Keeping original logic for now, but consider reviewing this.
              if (
                currentScreenshotIndex === screenshots.length - 1 &&
                hasMoreScreenshots
              ) {
                justLoadedMoreRef.current = true;
                fetchMoreScreenshots();
              } else if (currentScreenshotIndex < screenshots.length - 1) {
                setCurrentScreenshotIndex((prev) => prev + 1);
              }
            }}
            onGoForward={() =>
              setCurrentScreenshotIndex((prev) => Math.max(0, prev - 1))
            }
          />
        </View>
      ) : loadingScreenshots ? (
        // Show loading indicator during initial load
        <ActivityIndicator color={theme.colors.text.primary} />
      ) : (
        // Show empty text only if not loading and count is 0 or null
        <Text style={styles.emptyText}>No agent screenshots available.</Text>
      )}
    </View>
  );
};

const getStyles = (theme: Theme) =>
  StyleSheet.create({
    tabContentContainer: {
      flex: 1,
      alignItems: 'center',
    },
    errorText: {
      color: theme.colors.indicators.error,
      textAlign: 'center',
    },
    carouselContainer: {
      width: '100%',
      justifyContent: 'center',
      alignItems: 'center',
    },
    screenshotImageWrapper: {
      width: '100%',
      backgroundColor: theme.colors.layout.foreground,
      marginBottom: paddings.medium,
    },
    screenshotImage: {
      width: '100%',
      aspectRatio: 1280 / 1100,
    },
    emptyText: {
      color: theme.colors.text.secondary,
      textAlign: 'center',
    },
  }); 