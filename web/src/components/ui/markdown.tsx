"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter, SyntaxHighlighterProps } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface MarkdownProps {
  children: string;
  className?: string;
}

export function Markdown({ children, className }: MarkdownProps) {
  return (
    <ReactMarkdown
      className={className}
      remarkPlugins={[remarkGfm]}
      components={{
        // Code blocks with syntax highlighting
        code({ node, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const isInline = !match && !String(children).includes("\n");

          if (isInline) {
            return (
              <code
                className="px-1.5 py-0.5 rounded bg-muted font-mono text-sm"
                {...props}
              >
                {children}
              </code>
            );
          }

          return (
            <SyntaxHighlighter
              style={oneDark as SyntaxHighlighterProps["style"]}
              language={match?.[1] || "text"}
              PreTag="div"
              className="rounded-md text-sm !my-2"
            >
              {String(children).replace(/\n$/, "")}
            </SyntaxHighlighter>
          );
        },
        // Paragraphs
        p({ children }) {
          return <p className="mb-2 last:mb-0">{children}</p>;
        },
        // Headers
        h1({ children }) {
          return <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>;
        },
        h2({ children }) {
          return <h2 className="text-lg font-bold mt-3 mb-2">{children}</h2>;
        },
        h3({ children }) {
          return <h3 className="text-base font-bold mt-2 mb-1">{children}</h3>;
        },
        // Lists
        ul({ children }) {
          return <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>;
        },
        ol({ children }) {
          return <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>;
        },
        li({ children }) {
          return <li className="ml-2">{children}</li>;
        },
        // Links
        a({ href, children }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              {children}
            </a>
          );
        },
        // Blockquotes
        blockquote({ children }) {
          return (
            <blockquote className="border-l-4 border-muted-foreground/30 pl-4 italic my-2">
              {children}
            </blockquote>
          );
        },
        // Tables
        table({ children }) {
          return (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full border-collapse border border-border text-sm">
                {children}
              </table>
            </div>
          );
        },
        th({ children }) {
          return (
            <th className="border border-border bg-muted px-3 py-1.5 text-left font-medium">
              {children}
            </th>
          );
        },
        td({ children }) {
          return (
            <td className="border border-border px-3 py-1.5">{children}</td>
          );
        },
        // Horizontal rule
        hr() {
          return <hr className="my-4 border-border" />;
        },
        // Strong and emphasis
        strong({ children }) {
          return <strong className="font-semibold">{children}</strong>;
        },
        em({ children }) {
          return <em className="italic">{children}</em>;
        },
      }}
    >
      {children}
    </ReactMarkdown>
  );
}
