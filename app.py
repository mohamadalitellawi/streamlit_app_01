# app.py - Main application entry point
import streamlit as st
import os
from pathlib import Path
import importlib
import sys
from typing import Dict, Any, List, Optional, Union, Callable
import pandas as pd

# Set page config
st.set_page_config(
    page_title="Text File Processor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- Utility Functions ----
def load_file_from_upload() -> Optional[str]:
    """
    Load file content from Streamlit's file uploader.
    
    Returns:
        String content of the file or None if no file uploaded
    """
    uploaded_file = st.file_uploader("Upload text file", type=['txt', 'csv', 'log'])
    
    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            return content
        except Exception as e:
            st.error(f"Error processing uploaded file: {str(e)}")
            return None
    return None


def load_file_from_onedrive(link: str) -> Optional[str]:
    """
    Load file content from a OneDrive shared link.
    
    Args:
        link: OneDrive sharing link
        
    Returns:
        String content of the file or None if error occurs
    """
    try:
        import requests
        from urllib.parse import urlparse
        
        # Convert OneDrive sharing link to direct download link
        parsed_url = urlparse(link)
        if 'sharepoint.com' in parsed_url.netloc or '1drv.ms' in parsed_url.netloc:
            # For shortened URLs, we need to follow redirects
            if '1drv.ms' in parsed_url.netloc:
                response = requests.get(link, allow_redirects=True)
                link = response.url
            
            # Replace 'view.aspx' with 'download.aspx' to get direct download link
            download_link = link.replace('view.aspx', 'download.aspx')
            
            response = requests.get(download_link)
            response.raise_for_status()
            
            return response.text
        else:
            st.error("Invalid OneDrive share link format.")
            return None
    except Exception as e:
        st.error(f"Error reading from OneDrive: {str(e)}")
        return None


def save_dataframe_as_csv(df: pd.DataFrame) -> None:
    """
    Provide download button for DataFrame as CSV.
    
    Args:
        df: DataFrame to save
    """
    if df is not None and not df.empty:
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="result.csv",
            mime="text/csv"
        )


# ---- Page Base Class ----
class ProcessorPage:
    """Base class for processor pages."""
    
    def __init__(self, title: str):
        """
        Initialize processor page.
        
        Args:
            title: Page title
        """
        self.title = title
        self.content: Optional[str] = None
    
    def show(self) -> None:
        """Show the page."""
        st.title(self.title)
        
        # File upload section
        st.header("Upload File")
        tab1, tab2 = st.tabs(["Upload File", "OneDrive Link"])
        
        with tab1:
            uploaded_content = load_file_from_upload()
            if uploaded_content:
                self.content = uploaded_content
                st.success("File uploaded successfully!")
            
        with tab2:
            onedrive_link = st.text_input("OneDrive share link:")
            if onedrive_link and st.button("Load from OneDrive"):
                with st.spinner("Loading file from OneDrive..."):
                    onedrive_content = load_file_from_onedrive(onedrive_link)
                    if onedrive_content:
                        self.content = onedrive_content
                        st.success("File loaded from OneDrive successfully!")
        
        # Parameters section
        st.header("Processing Parameters")
        parameters = self.render_parameters()
        
        # Process button
        if self.content and st.button("Process Data"):
            with st.spinner("Processing..."):
                try:
                    result = self.process_text(self.content, parameters)
                    if result is not None:
                        st.success("Processing complete!")
                        st.subheader("Results")
                        st.dataframe(result)
                        save_dataframe_as_csv(result)
                except Exception as e:
                    import traceback
                    st.error(f"Error during processing: {str(e)}")
                    st.error(traceback.format_exc())
    
    def render_parameters(self) -> Dict[str, Any]:
        """
        Render parameter controls.
        
        Returns:
            Dictionary of parameters
        """
        # Override in subclasses
        return {}
    
    def process_text(self, text: str, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Process text based on parameters.
        
        Args:
            text: Input text to process
            params: Processing parameters
            
        Returns:
            DataFrame with processed results
        """
        # Override in subclasses
        raise NotImplementedError("Process method must be implemented by subclasses")


# ---- Page Registry ----
class PageRegistry:
    """Registry for application pages."""
    
    _pages: Dict[str, ProcessorPage] = {}
    
    @classmethod
    def register(cls, page: ProcessorPage) -> None:
        """
        Register a page.
        
        Args:
            page: ProcessorPage instance
        """
        cls._pages[page.title] = page
    
    @classmethod
    def get_pages(cls) -> Dict[str, ProcessorPage]:
        """
        Get all registered pages.
        
        Returns:
            Dictionary of page titles and instances
        """
        return cls._pages


# ---- Example Processor Pages ----
class WordCountPage(ProcessorPage):
    """Page for word count analysis."""
    
    def __init__(self):
        super().__init__("Word Count Analysis")
    
    def render_parameters(self) -> Dict[str, Any]:
        """Render parameter controls for word count analysis."""
        params = {}
        
        params['min_length'] = st.slider(
            "Minimum word length",
            min_value=1,
            max_value=10,
            value=3,
            help="Minimum number of characters for a word to be counted"
        )
        
        params['ignore_case'] = st.checkbox(
            "Ignore case (convert all to lowercase)",
            value=True,
            help="Convert all text to lowercase before counting"
        )
        
        return params
    
    def process_text(self, text: str, params: Dict[str, Any]) -> pd.DataFrame:
        """Process text for word count analysis."""
        # Get parameters
        min_length = params.get('min_length', 1)
        ignore_case = params.get('ignore_case', True)
        
        # Process text
        if ignore_case:
            text = text.lower()
        
        # Split text into words and filter by minimum length
        words = [word.strip(r'.,!?()[]{}:;"\'') for word in text.split()]
        words = [word for word in words if len(word) >= min_length]
        
        # Count word frequencies
        word_counts = {}
        for word in words:
            if word:  # Ignore empty strings
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Convert to DataFrame
        result = pd.DataFrame({
            'word': list(word_counts.keys()),
            'count': list(word_counts.values())
        })
        
        # Sort by count in descending order
        result = result.sort_values('count', ascending=False).reset_index(drop=True)
        
        return result


class SentimentAnalysisPage(ProcessorPage):
    """Page for sentiment analysis."""
    
    def __init__(self):
        super().__init__("Sentiment Analysis")
    
    def render_parameters(self) -> Dict[str, Any]:
        """Render parameter controls for sentiment analysis."""
        params = {}
        
        params['chunk_size'] = st.slider(
            "Text chunk size (characters)",
            min_value=50,
            max_value=500,
            value=100,
            step=50,
            help="Number of characters per analyzed chunk"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            params['positive_words'] = st.text_area(
                "Positive words (comma-separated)",
                value="good,great,excellent,happy,positive",
                help="List of words that indicate positive sentiment"
            )
            
        with col2:
            params['negative_words'] = st.text_area(
                "Negative words (comma-separated)",
                value="bad,poor,terrible,sad,negative",
                help="List of words that indicate negative sentiment"
            )
        
        return params
    
    def process_text(self, text: str, params: Dict[str, Any]) -> pd.DataFrame:
        """Process text for sentiment analysis."""
        # Get parameters
        chunk_size = params.get('chunk_size', 100)
        positive_words = set(params.get('positive_words', '').lower().split(','))
        negative_words = set(params.get('negative_words', '').lower().split(','))
        
        # Clean input lists
        positive_words = {word.strip() for word in positive_words if word.strip()}
        negative_words = {word.strip() for word in negative_words if word.strip()}
        
        # Default word lists if none provided
        if not positive_words:
            positive_words = {'good', 'great', 'excellent', 'happy', 'positive'}
        if not negative_words:
            negative_words = {'bad', 'poor', 'terrible', 'sad', 'negative'}
        
        # Split text into chunks
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        results = []
        for i, chunk in enumerate(chunks):
            chunk_lower = chunk.lower()
            # Count positive and negative words
            pos_count = sum(1 for word in positive_words if word in chunk_lower)
            neg_count = sum(1 for word in negative_words if word in chunk_lower)
            
            # Calculate sentiment score (-1 to 1)
            total = pos_count + neg_count
            sentiment_score = 0
            if total > 0:
                sentiment_score = (pos_count - neg_count) / total
            
            results.append({
                'chunk_id': i + 1,
                'text': chunk[:50] + '...' if len(chunk) > 50 else chunk,
                'positive_words': pos_count,
                'negative_words': neg_count,
                'sentiment_score': sentiment_score
            })
        
        return pd.DataFrame(results)


class TextStatisticsPage(ProcessorPage):
    """Page for text statistics analysis."""
    
    def __init__(self):
        super().__init__("Text Statistics")
    
    def render_parameters(self) -> Dict[str, Any]:
        """Render parameter controls for text statistics."""
        params = {}
        
        params['count_paragraphs'] = st.checkbox(
            "Count paragraphs",
            value=True
        )
        
        params['count_sentences'] = st.checkbox(
            "Count sentences",
            value=True
        )
        
        params['count_words'] = st.checkbox(
            "Count words",
            value=True
        )
        
        params['count_chars'] = st.checkbox(
            "Count characters",
            value=True
        )
        
        params['include_whitespace'] = st.checkbox(
            "Include whitespace in character count",
            value=False
        )
        
        return params
    
    def process_text(self, text: str, params: Dict[str, Any]) -> pd.DataFrame:
        """Process text for statistics analysis."""
        import re
        
        results = []
        
        # Count paragraphs (separated by one or more newlines)
        if params.get('count_paragraphs', True):
            paragraphs = re.split(r'\n\s*\n', text)
            paragraphs = [p for p in paragraphs if p.strip()]
            results.append({
                'statistic': 'Paragraphs',
                'count': len(paragraphs)
            })
        
        # Count sentences (naive implementation - split by .!?)
        if params.get('count_sentences', True):
            sentences = re.split(r'[.!?]+', text)
            sentences = [s for s in sentences if s.strip()]
            results.append({
                'statistic': 'Sentences',
                'count': len(sentences)
            })
        
        # Count words
        if params.get('count_words', True):
            words = re.findall(r'\b\w+\b', text)
            results.append({
                'statistic': 'Words',
                'count': len(words)
            })
        
        # Count characters
        if params.get('count_chars', True):
            if params.get('include_whitespace', False):
                char_count = len(text)
            else:
                char_count = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
            
            results.append({
                'statistic': 'Characters',
                'count': char_count
            })
        
        return pd.DataFrame(results)


# ---- Main App ----
def main() -> None:
    """Main application function."""
    # Register pages
    PageRegistry.register(WordCountPage())
    PageRegistry.register(SentimentAnalysisPage())
    PageRegistry.register(TextStatisticsPage())
    
    # Sidebar navigation
    st.sidebar.title("Text File Processor")
    st.sidebar.header("Navigation")
    
    pages = PageRegistry.get_pages()
    selection = st.sidebar.radio("Select a processor:", list(pages.keys()))
    
    # Show the selected page
    selected_page = pages.get(selection)
    if selected_page:
        selected_page.show()

if __name__ == "__main__":
    main()