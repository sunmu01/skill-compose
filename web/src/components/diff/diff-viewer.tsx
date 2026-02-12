'use client';

import dynamic from 'next/dynamic';

// Dynamically import to avoid SSR issues
const ReactDiffViewer = dynamic(
  () => import('react-diff-viewer-continued').then((mod) => mod.default),
  { ssr: false, loading: () => <div className="p-4 text-center text-muted-foreground">Loading diff viewer...</div> }
);

interface DiffViewerProps {
  oldValue: string;
  newValue: string;
  oldTitle?: string;
  newTitle?: string;
  splitView?: boolean;
  showDiffOnly?: boolean;
}

// Custom styles for the diff viewer
const diffStyles = {
  variables: {
    dark: {
      diffViewerBackground: '#1e1e1e',
      diffViewerColor: '#d4d4d4',
      addedBackground: '#1e3a1e',
      addedColor: '#98c379',
      removedBackground: '#3a1e1e',
      removedColor: '#e06c75',
      wordAddedBackground: '#2d5a2d',
      wordRemovedBackground: '#5a2d2d',
      addedGutterBackground: '#2d4a2d',
      removedGutterBackground: '#4a2d2d',
      gutterBackground: '#252526',
      gutterColor: '#858585',
      codeFoldBackground: '#2d2d2d',
      codeFoldGutterBackground: '#2d2d2d',
      codeFoldContentColor: '#858585',
      emptyLineBackground: '#1e1e1e',
    },
    light: {
      diffViewerBackground: '#ffffff',
      diffViewerColor: '#1f2328',
      addedBackground: '#dafbe1',
      addedColor: '#1a7f37',
      removedBackground: '#ffebe9',
      removedColor: '#cf222e',
      wordAddedBackground: '#aceebb',
      wordRemovedBackground: '#ffc0c0',
      addedGutterBackground: '#ccffd8',
      removedGutterBackground: '#ffd7d5',
      gutterBackground: '#f6f8fa',
      gutterColor: '#656d76',
      codeFoldBackground: '#f6f8fa',
      codeFoldGutterBackground: '#f6f8fa',
      codeFoldContentColor: '#656d76',
      emptyLineBackground: '#ffffff',
    },
  },
  line: {
    padding: '4px 8px',
    fontSize: '13px',
    fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, monospace',
  },
  gutter: {
    padding: '4px 12px',
    minWidth: '40px',
  },
  marker: {
    padding: '4px 8px',
  },
  contentText: {
    fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, monospace',
  },
};

export function DiffViewer({
  oldValue,
  newValue,
  oldTitle,
  newTitle,
  splitView = true,
  showDiffOnly = true,
}: DiffViewerProps) {
  return (
    <div className="rounded-lg border overflow-hidden">
      <ReactDiffViewer
        oldValue={oldValue}
        newValue={newValue}
        leftTitle={oldTitle}
        rightTitle={newTitle}
        splitView={splitView}
        useDarkTheme={true}
        styles={diffStyles}
        compareMethod={"diffWords" as any}
        showDiffOnly={showDiffOnly}
        extraLinesSurroundingDiff={3}
      />
    </div>
  );
}

export default DiffViewer;
