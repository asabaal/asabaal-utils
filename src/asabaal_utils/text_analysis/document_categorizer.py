#!/usr/bin/env python3
"""
Generic Document Categorization System
A flexible, unsupervised system for categorizing any type of documents
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter
from abc import ABC, abstractmethod
import warnings
warnings.filterwarnings('ignore')

# Machine learning imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

class DocumentCategorizationSystem(ABC):
    """
    Abstract base class for document categorization systems
    
    Provides core categorization algorithms and splitting strategies.
    Subclasses implement domain-specific preprocessing and naming logic.
    """
    
    def __init__(self, min_clusters: int = 3, max_clusters: int = 15):
        """
        Initialize the categorization system
        
        Args:
            min_clusters: Minimum number of categories to discover
            max_clusters: Maximum number of categories to discover
        """
        self.categories = {}
        self.min_clusters = min_clusters
        self.max_clusters = max_clusters
        self.vectorizer = None
        self.cluster_model = None
        self.topic_model = None
        self.df = pd.DataFrame()
        self.color_palette = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', 
            '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43', '#EE5A24', '#0984E3',
            '#A29BFE', '#FD79A8', '#FDCB6E', '#6C5CE7', '#74B9FF', '#00B894'
        ]
    
    @abstractmethod
    def clean_document(self, document: str) -> str:
        """
        Clean and normalize a single document
        
        Args:
            document: Raw document text
            
        Returns:
            Cleaned document text
        """
        pass
    
    @abstractmethod
    def preprocess_document(self, document: str) -> str:
        """
        Preprocess document for categorization (tokenization, stemming, etc.)
        
        Args:
            document: Cleaned document text
            
        Returns:
            Preprocessed document text
        """
        pass
    
    @abstractmethod
    def generate_category_name(self, features: List[str], sample_documents: List[str]) -> str:
        """
        Generate a meaningful category name from features and sample documents
        
        Args:
            features: Top features/keywords for the category
            sample_documents: Sample documents from the category
            
        Returns:
            Generated category name
        """
        pass
    
    @abstractmethod
    def get_category_icon(self, features: List[str]) -> str:
        """
        Get appropriate icon for category based on features
        
        Args:
            features: Top features for the category
            
        Returns:
            Unicode icon or emoji
        """
        pass
    
    def load_documents(self, documents: List[str], document_ids: Optional[List[Any]] = None, 
                      dates: Optional[List[datetime]] = None, metadata: Optional[Dict] = None):
        """
        Load documents into the system
        
        Args:
            documents: List of document texts
            document_ids: Optional list of document IDs
            dates: Optional list of document dates
            metadata: Optional metadata dictionary
        """
        # Clean documents
        cleaned_documents = []
        original_documents = []
        
        for doc in documents:
            cleaned = self.clean_document(doc)
            if cleaned:  # Only keep non-empty cleaned documents
                cleaned_documents.append(cleaned)
                original_documents.append(doc)
        
        print(f"🧹 Cleaned {len(documents)} documents -> {len(cleaned_documents)} valid documents")
        
        if not cleaned_documents:
            print("❌ No valid documents after cleaning")
            self.df = pd.DataFrame()
            return
        
        # Create DataFrame
        data = []
        for i, (original, cleaned) in enumerate(zip(original_documents, cleaned_documents)):
            # Use provided IDs or generate them
            doc_id = document_ids[i] if document_ids and i < len(document_ids) else i
            
            # Use provided dates or simulate them
            if dates and i < len(dates):
                date = dates[i]
            else:
                # Simulate dates for demo
                days_ago = np.random.randint(0, 365)
                date = datetime.now() - timedelta(days=days_ago)
            
            data.append({
                'id': doc_id,
                'original_document': original,
                'document': cleaned,
                'cleaned_document': cleaned,
                'date': date,
                'word_count': len(cleaned.split()),
                'char_count': len(cleaned),
                'category': 'Uncategorized'
            })
        
        self.df = pd.DataFrame(data)
        
        # Discover categories
        if len(self.df) >= self.min_clusters:
            print("🔍 Discovering categories from your documents...")
            discovered_categories = self.discover_categories_unsupervised(method='both')
            
            if discovered_categories:
                self.categories = discovered_categories
                self._assign_categories_to_documents()
                print(f"✅ Discovered {len(discovered_categories)} categories")
                
                # Apply recursive subcategorization
                print(f"🔄 Starting recursive subcategorization...")
                self.apply_recursive_subcategorization(max_category_pct=0.1, min_category_pct=0.01)
            else:
                print("❌ Could not discover categories from data")
        else:
            print(f"❌ Need at least {self.min_clusters} documents for category discovery")
        
        self._print_summary()
    
    def discover_categories_unsupervised(self, method: str = 'both') -> Dict:
        """
        Discover categories using unsupervised methods
        
        Args:
            method: 'kmeans', 'lda', or 'both'
            
        Returns:
            Dictionary with discovered categories
        """
        if self.df.empty or len(self.df) < self.min_clusters:
            print(f"❌ Need at least {self.min_clusters} documents for category discovery")
            return {}
        
        # Prepare text data
        cleaned_documents = [self.preprocess_document(doc) for doc in self.df['cleaned_document']]
        cleaned_documents = [doc for doc in cleaned_documents if len(doc) > 0]
        
        if len(cleaned_documents) < self.min_clusters:
            print("❌ Not enough valid documents after preprocessing")
            return {}
        
        print(f"🔍 Analyzing {len(cleaned_documents)} documents...")
        
        # Create TF-IDF vectors
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8,
            stop_words='english'
        )
        
        tfidf_matrix = self.vectorizer.fit_transform(cleaned_documents)
        feature_names = self.vectorizer.get_feature_names_out()
        
        discovered_categories = {}
        
        # K-means clustering approach
        if method in ['kmeans', 'both']:
            kmeans_categories = self._discover_with_kmeans(tfidf_matrix, feature_names, cleaned_documents)
            discovered_categories.update(kmeans_categories)
        
        # LDA topic modeling approach
        if method in ['lda', 'both']:
            lda_categories = self._discover_with_lda(cleaned_documents, feature_names)
            if method == 'both':
                discovered_categories = self._merge_category_insights(discovered_categories, lda_categories)
            else:
                discovered_categories.update(lda_categories)
        
        return discovered_categories
    
    def _discover_with_kmeans(self, tfidf_matrix, feature_names: List[str], cleaned_documents: List[str]) -> Dict:
        """K-means clustering for category discovery"""
        silhouette_scores = []
        K_range = range(self.min_clusters, min(self.max_clusters + 1, len(cleaned_documents) // 2))
        
        best_k = self.min_clusters
        best_score = -1
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(tfidf_matrix)
            
            if len(set(labels)) > 1:
                score = silhouette_score(tfidf_matrix, labels)
                silhouette_scores.append((k, score))
                if score > best_score:
                    best_score = score
                    best_k = k
        
        print(f"📊 Optimal number of categories: {best_k} (silhouette score: {best_score:.3f})")
        
        # Perform final clustering
        self.cluster_model = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        cluster_labels = self.cluster_model.fit_predict(tfidf_matrix)
        
        # Create categories from clusters
        categories = {}
        for i in range(best_k):
            cluster_center = self.cluster_model.cluster_centers_[i]
            top_features_idx = cluster_center.argsort()[-10:][::-1]
            top_features = [feature_names[idx] for idx in top_features_idx]
            
            cluster_documents = [cleaned_documents[j] for j in range(len(cleaned_documents)) if cluster_labels[j] == i]
            category_name = self.generate_category_name(top_features, cluster_documents)
            
            categories[category_name] = {
                'keywords': top_features,
                'color': self.color_palette[i % len(self.color_palette)],
                'icon': self.get_category_icon(top_features),
                'cluster_id': i,
                'size': sum(cluster_labels == i),
                'method': 'kmeans',
                'document_indices': [j for j in range(len(cleaned_documents)) if cluster_labels[j] == i]
            }
        
        return categories
    
    def _discover_with_lda(self, cleaned_documents: List[str], feature_names: List[str]) -> Dict:
        """LDA topic modeling for category discovery"""
        best_perplexity = float('inf')
        best_n_topics = self.min_clusters
        
        for n_topics in range(self.min_clusters, min(self.max_clusters + 1, len(cleaned_documents) // 2)):
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=100,
                learning_method='online'
            )
            
            tfidf_matrix = self.vectorizer.transform(cleaned_documents)
            lda.fit(tfidf_matrix)
            
            perplexity = lda.perplexity(tfidf_matrix)
            if perplexity < best_perplexity:
                best_perplexity = perplexity
                best_n_topics = n_topics
        
        print(f"📊 Optimal number of topics (LDA): {best_n_topics} (perplexity: {best_perplexity:.3f})")
        
        # Fit final LDA model
        self.topic_model = LatentDirichletAllocation(
            n_components=best_n_topics,
            random_state=42,
            max_iter=100,
            learning_method='online'
        )
        
        tfidf_matrix = self.vectorizer.transform(cleaned_documents)
        self.topic_model.fit(tfidf_matrix)
        
        # Get topic assignments
        topic_assignments = self.topic_model.transform(tfidf_matrix)
        dominant_topics = topic_assignments.argmax(axis=1)
        
        # Create categories from topics
        categories = {}
        for i in range(best_n_topics):
            top_words_idx = self.topic_model.components_[i].argsort()[-10:][::-1]
            top_words = [feature_names[idx] for idx in top_words_idx]
            
            topic_documents = [cleaned_documents[j] for j in range(len(cleaned_documents)) if dominant_topics[j] == i]
            category_name = self.generate_category_name(top_words, topic_documents)
            
            categories[category_name] = {
                'keywords': top_words,
                'color': self.color_palette[i % len(self.color_palette)],
                'icon': self.get_category_icon(top_words),
                'topic_id': i,
                'size': sum(dominant_topics == i),
                'method': 'lda',
                'document_indices': [j for j in range(len(cleaned_documents)) if dominant_topics[j] == i]
            }
        
        return categories
    
    def _merge_category_insights(self, kmeans_categories: Dict, lda_categories: Dict) -> Dict:
        """Merge insights from K-means and LDA"""
        merged = kmeans_categories.copy()
        
        for cat_name, cat_data in merged.items():
            kmeans_keywords = set(cat_data['keywords'])
            
            for lda_name, lda_data in lda_categories.items():
                lda_keywords = set(lda_data['keywords'])
                overlap = len(kmeans_keywords.intersection(lda_keywords))
                
                if overlap > 2:
                    merged_keywords = list(kmeans_keywords.union(lda_keywords))
                    merged[cat_name]['keywords'] = merged_keywords[:10]
                    merged[cat_name]['method'] = 'kmeans+lda'
        
        return merged
    
    def apply_recursive_subcategorization(self, max_category_pct: float = 0.1, min_category_pct: float = 0.01):
        """
        Recursively split large categories until all are within target range
        
        Args:
            max_category_pct: Maximum percentage a category can represent (0.1 = 10%)
            min_category_pct: Minimum percentage a category should have (0.01 = 1%)
        """
        if self.df.empty:
            print("❌ No data available")
            return
        
        total_docs = len(self.df)
        max_size = int(total_docs * max_category_pct)
        min_size = int(total_docs * min_category_pct)
        
        print(f"🔄 Breaking down categories over {max_category_pct*100}% ({max_size} documents)")
        print(f"📊 Minimum size for splitting: {min_category_pct*100}% ({min_size} documents)")
        
        iteration = 0
        while True:
            iteration += 1
            print(f"\n📊 Iteration {iteration}:")
            
            # Check current category sizes
            category_counts = self.df['category'].value_counts()
            large_categories = [(cat, count) for cat, count in category_counts.items() 
                              if count > max_size]
            
            if not large_categories:
                print("✅ All categories are now under the threshold!")
                break
            
            print(f"Found {len(large_categories)} large categories:")
            for cat, count in large_categories:
                pct = (count / total_docs) * 100
                print(f"   - {cat}: {count} documents ({pct:.1f}%)")
            
            # Split each large category
            splits_made = 0
            for category_name, category_size in large_categories:
                category_pct = (category_size / total_docs) * 100
                
                # Calculate dynamic minimum size while ALWAYS respecting 1% threshold
                if category_pct > 20:  # >20% - be very aggressive
                    aggressive_min = max(min_size, min_size // 2)
                    dynamic_min_size = aggressive_min
                    print(f"   Using aggressive splitting for {category_name} ({category_pct:.1f}%) - min size: {dynamic_min_size}")
                elif category_pct > 15:  # >15% - be moderately aggressive  
                    aggressive_min = max(min_size, int(min_size * 0.75))
                    dynamic_min_size = aggressive_min
                    print(f"   Using moderate splitting for {category_name} ({category_pct:.1f}%) - min size: {dynamic_min_size}")
                else:
                    dynamic_min_size = min_size
                    print(f"   Using standard splitting for {category_name} ({category_pct:.1f}%) - min size: {dynamic_min_size}")
                
                # Double-check: Never allow subcategories below 1% threshold
                if dynamic_min_size < min_size:
                    print(f"   ⚠️  Adjusting min size from {dynamic_min_size} to {min_size} to respect 1% threshold")
                    dynamic_min_size = min_size
                
                # Check if this category can even be split while respecting minimums
                theoretical_max_subcats = category_size // dynamic_min_size
                if theoretical_max_subcats < 2:
                    print(f"   ⚠️  {category_name} ({category_size} documents) cannot be split while respecting 1% minimum ({dynamic_min_size} documents)")
                    print(f"      Would need at least {dynamic_min_size * 2} documents to split into 2 subcategories")
                    continue
                
                print(f"   Splitting {category_name}...")
                
                # Get documents in this category
                category_docs = self.df[self.df['category'] == category_name].copy()
                
                # Try to split it
                subcategories = self._create_subcategories_enhanced(category_docs, category_name, iteration, dynamic_min_size)
                
                if subcategories and len(subcategories) > 1:
                    print(f"   ✅ Split into {len(subcategories)} subcategories")
                    
                    # Update the dataframe
                    for subcat_name, subcat_data in subcategories.items():
                        doc_ids = subcat_data.get('document_ids', [])
                        for doc_id in doc_ids:
                            self.df.loc[self.df['id'] == doc_id, 'category'] = subcat_name
                    
                    # Update categories dictionary
                    for subcat_name, subcat_data in subcategories.items():
                        self.categories[subcat_name] = subcat_data
                    
                    # Remove old category
                    if category_name in self.categories:
                        del self.categories[category_name]
                    
                    splits_made += 1
                else:
                    print(f"   ❌ Could not split {category_name}")
            
            if splits_made == 0:
                print("⚠️  No categories could be split further")
                break
            
            print(f"Made {splits_made} splits this iteration")
        
        print(f"\n🎉 Subcategorization complete after {iteration} iterations!")
        
        # Final size analysis
        final_category_counts = self.df['category'].value_counts()
        total_docs = len(self.df)
        
        over_threshold = []
        under_threshold = []
        in_range = []
        
        for cat, count in final_category_counts.items():
            pct = (count / total_docs) * 100
            if pct > max_category_pct * 100:
                over_threshold.append((cat, count, pct))
            elif pct < min_category_pct * 100:
                under_threshold.append((cat, count, pct))
            else:
                in_range.append((cat, count, pct))
        
        print(f"\n📊 Final size analysis:")
        print(f"   ✅ {len(in_range)} categories in target range (1%-10%)")
        
        if over_threshold:
            print(f"   ⚠️  {len(over_threshold)} categories still over 10%:")
            for cat, count, pct in over_threshold:
                print(f"      - {cat}: {count} documents ({pct:.1f}%) - couldn't split while respecting 1% minimum")
        
        if under_threshold:
            print(f"   ⚠️  {len(under_threshold)} categories under 1%:")
            for cat, count, pct in under_threshold:
                print(f"      - {cat}: {count} documents ({pct:.1f}%) - created during splitting process")
        
        self._print_summary()
    
    def _create_subcategories_enhanced(self, category_docs: pd.DataFrame, parent_category: str, depth: int, min_size_override: int) -> Dict:
        """
        Enhanced subcategory creation with multiple fallback strategies
        """
        # Prepare text data
        documents = category_docs['cleaned_document'].tolist()
        processed_documents = [self.preprocess_document(doc) for doc in documents]
        processed_documents = [doc for doc in processed_documents if len(doc) > 0]
        
        if len(processed_documents) < self.min_clusters:
            return {}
        
        if len(category_docs) < min_size_override:
            print(f"   Category too small to split ({len(category_docs)} < {min_size_override})")
            return {}
        
        # Strategy 1: Standard K-means clustering
        subcategories = self._try_kmeans_clustering(processed_documents, category_docs, parent_category, depth, min_size_override)
        if subcategories and len(subcategories) >= 2:
            print(f"   ✅ K-means succeeded with {len(subcategories)} subcategories")
            return subcategories
        
        # Strategy 2: Hierarchical clustering
        print(f"   K-means failed, trying hierarchical clustering...")
        subcategories = self._try_hierarchical_clustering(processed_documents, category_docs, parent_category, depth, min_size_override)
        if subcategories and len(subcategories) >= 2:
            print(f"   ✅ Hierarchical clustering succeeded with {len(subcategories)} subcategories")
            return subcategories
        
        # Strategy 3: Length-based splitting
        print(f"   Hierarchical failed, trying length-based splitting...")
        subcategories = self._try_length_based_splitting(category_docs, parent_category, depth, min_size_override)
        if subcategories and len(subcategories) >= 2:
            print(f"   ✅ Length-based splitting succeeded with {len(subcategories)} subcategories")
            return subcategories
        
        # Strategy 4: Alphabetical force split
        print(f"   Length-based failed, trying alphabetical force split...")
        subcategories = self._try_alphabetical_force_split(category_docs, parent_category, depth, min_size_override)
        if subcategories and len(subcategories) >= 2:
            print(f"   ✅ Alphabetical force split succeeded with {len(subcategories)} subcategories")
            return subcategories
        
        # Strategy 5: Temporal splitting
        print(f"   Alphabetical failed, trying temporal splitting...")
        subcategories = self._try_temporal_splitting(category_docs, parent_category, depth, min_size_override)
        if subcategories and len(subcategories) >= 2:
            print(f"   ✅ Temporal splitting succeeded with {len(subcategories)} subcategories")
            return subcategories
        
        print(f"   ❌ All splitting strategies failed")
        return {}
    
    def _try_kmeans_clustering(self, processed_documents: List[str], category_docs: pd.DataFrame, parent_category: str, depth: int, min_size_override: int) -> Dict:
        """Try K-means clustering with multiple parameter sets"""
        vectorizers = [
            TfidfVectorizer(max_features=500, ngram_range=(1, 2), min_df=1, max_df=0.9, stop_words='english'),
            TfidfVectorizer(max_features=300, ngram_range=(1, 3), min_df=1, max_df=0.95, stop_words='english'),
            TfidfVectorizer(max_features=200, ngram_range=(1, 1), min_df=1, max_df=1.0, stop_words='english')
        ]
        
        for vec_idx, vectorizer in enumerate(vectorizers):
            try:
                tfidf_matrix = vectorizer.fit_transform(processed_documents)
                feature_names = vectorizer.get_feature_names_out()
                
                best_result = None
                best_valid_count = 0
                
                max_clusters = min(15, len(processed_documents) // max(2, min_size_override // 3))
                K_range = range(2, max_clusters + 1)
                
                for k in K_range:
                    kmeans = KMeans(n_clusters=k, random_state=42 + vec_idx, n_init=10)
                    labels = kmeans.fit_predict(tfidf_matrix)
                    
                    valid_count = 0
                    test_subcategories = {}
                    
                    for i in range(k):
                        cluster_indices = [j for j in range(len(processed_documents)) if labels[j] == i]
                        if len(cluster_indices) >= min_size_override:
                            valid_count += 1
                            
                            doc_ids = [category_docs.iloc[j]['id'] for j in cluster_indices]
                            cluster_center = kmeans.cluster_centers_[i]
                            top_features_idx = cluster_center.argsort()[-10:][::-1]
                            top_features = [feature_names[idx] for idx in top_features_idx]
                            
                            subcat_name = self._generate_subcategory_name(parent_category, top_features, depth, i)
                            test_subcategories[subcat_name] = {
                                'keywords': top_features,
                                'color': self.color_palette[(hash(subcat_name) % len(self.color_palette))],
                                'icon': self.get_category_icon(top_features),
                                'size': len(cluster_indices),
                                'method': f'enhanced_kmeans_v{vec_idx}_depth_{depth}',
                                'parent_category': parent_category,
                                'document_ids': doc_ids
                            }
                    
                    if valid_count >= 2 and valid_count > best_valid_count:
                        best_valid_count = valid_count
                        best_result = test_subcategories
                
                if best_result:
                    return best_result
                    
            except Exception as e:
                continue
        
        return {}
    
    def _try_hierarchical_clustering(self, processed_documents: List[str], category_docs: pd.DataFrame, parent_category: str, depth: int, min_size_override: int) -> Dict:
        """Try hierarchical clustering"""
        try:
            vectorizer = TfidfVectorizer(max_features=300, ngram_range=(1, 2), min_df=1, max_df=0.95, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(processed_documents)
            feature_names = vectorizer.get_feature_names_out()
            
            max_clusters = min(10, len(processed_documents) // max(2, min_size_override // 2))
            
            for n_clusters in range(2, max_clusters + 1):
                hierarchical = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
                
                dense_matrix = tfidf_matrix.toarray()
                labels = hierarchical.fit_predict(dense_matrix)
                
                valid_count = 0
                subcategories = {}
                
                for i in range(n_clusters):
                    cluster_indices = [j for j in range(len(processed_documents)) if labels[j] == i]
                    if len(cluster_indices) >= min_size_override:
                        valid_count += 1
                        
                        doc_ids = [category_docs.iloc[j]['id'] for j in cluster_indices]
                        
                        cluster_vectors = tfidf_matrix[cluster_indices]
                        mean_vector = cluster_vectors.mean(axis=0).A1
                        top_features_idx = mean_vector.argsort()[-10:][::-1]
                        top_features = [feature_names[idx] for idx in top_features_idx]
                        
                        subcat_name = self._generate_subcategory_name(parent_category, top_features, depth, i)
                        subcategories[subcat_name] = {
                            'keywords': top_features,
                            'color': self.color_palette[(hash(subcat_name) % len(self.color_palette))],
                            'icon': self.get_category_icon(top_features),
                            'size': len(cluster_indices),
                            'method': f'hierarchical_depth_{depth}',
                            'parent_category': parent_category,
                            'document_ids': doc_ids
                        }
                
                if valid_count >= 2:
                    return subcategories
                    
        except Exception as e:
            pass
        
        return {}
    
    def _try_length_based_splitting(self, category_docs: pd.DataFrame, parent_category: str, depth: int, min_size_override: int) -> Dict:
        """Split based on document length characteristics"""
        try:
            category_docs_copy = category_docs.copy()
            category_docs_copy['doc_length'] = category_docs_copy['cleaned_document'].str.len()
            
            short_threshold = category_docs_copy['doc_length'].quantile(0.33)
            long_threshold = category_docs_copy['doc_length'].quantile(0.67)
            
            length_groups = {
                'Short': category_docs_copy[category_docs_copy['doc_length'] <= short_threshold],
                'Medium': category_docs_copy[(category_docs_copy['doc_length'] > short_threshold) & 
                                           (category_docs_copy['doc_length'] <= long_threshold)],
                'Long': category_docs_copy[category_docs_copy['doc_length'] > long_threshold]
            }
            
            valid_groups = {name: group for name, group in length_groups.items() 
                          if len(group) >= min_size_override}
            
            if len(valid_groups) >= 2:
                subcategories = {}
                for i, (length_type, group) in enumerate(valid_groups.items()):
                    subcat_name = f"{parent_category}: {length_type} Length"
                    doc_ids = group['id'].tolist()
                    
                    subcategories[subcat_name] = {
                        'keywords': [length_type.lower(), 'length', 'document'],
                        'color': self.color_palette[(hash(subcat_name) % len(self.color_palette))],
                        'icon': '📏',
                        'size': len(group),
                        'method': f'length_based_depth_{depth}',
                        'parent_category': parent_category,
                        'document_ids': doc_ids
                    }
                
                return subcategories
            else:
                # Try 2-way split
                median_length = category_docs_copy['doc_length'].median()
                
                short_group = category_docs_copy[category_docs_copy['doc_length'] <= median_length]
                long_group = category_docs_copy[category_docs_copy['doc_length'] > median_length]
                
                if len(short_group) >= min_size_override and len(long_group) >= min_size_override:
                    subcategories = {}
                    for group_name, group in [('Short', short_group), ('Long', long_group)]:
                        subcat_name = f"{parent_category}: {group_name} Length"
                        doc_ids = group['id'].tolist()
                        
                        subcategories[subcat_name] = {
                            'keywords': [group_name.lower(), 'length', 'document'],
                            'color': self.color_palette[(hash(subcat_name) % len(self.color_palette))],
                            'icon': '📏',
                            'size': len(group),
                            'method': f'length_based_binary_depth_{depth}',
                            'parent_category': parent_category,
                            'document_ids': doc_ids
                        }
                    
                    return subcategories
                
        except Exception as e:
            pass
        
        return {}
    
    def _try_alphabetical_force_split(self, category_docs: pd.DataFrame, parent_category: str, depth: int, min_size_override: int) -> Dict:
        """Force split alphabetically when all else fails"""
        try:
            sorted_docs = category_docs.sort_values('cleaned_document')
            total_docs = len(sorted_docs)
            
            max_groups = total_docs // min_size_override
            if max_groups < 2:
                print(f"      Cannot split alphabetically: need {min_size_override * 2} documents minimum, have {total_docs}")
                return {}
            
            best_split = None
            
            for num_groups in range(2, min(max_groups + 1, 4)):
                group_size = total_docs // num_groups
                remainder = total_docs % num_groups
                
                smallest_group_size = group_size
                if smallest_group_size >= min_size_override:
                    subcategories = {}
                    current_idx = 0
                    
                    for i in range(num_groups):
                        current_group_size = group_size + (1 if i < remainder else 0)
                        
                        if i == num_groups - 1:
                            group_docs = sorted_docs.iloc[current_idx:]
                        else:
                            group_docs = sorted_docs.iloc[current_idx:current_idx + current_group_size]
                        
                        current_idx += current_group_size
                        
                        if len(group_docs) >= min_size_override:
                            first_char = group_docs.iloc[0]['cleaned_document'][0].upper()
                            last_char = group_docs.iloc[-1]['cleaned_document'][0].upper()
                            
                            if first_char == last_char:
                                subcat_name = f"{parent_category}: {first_char}*"
                            else:
                                subcat_name = f"{parent_category}: {first_char}-{last_char}"
                            
                            doc_ids = group_docs['id'].tolist()
                            
                            subcategories[subcat_name] = {
                                'keywords': ['alphabetical', 'sorted', first_char.lower()],
                                'color': self.color_palette[(hash(subcat_name) % len(self.color_palette))],
                                'icon': '🔤',
                                'size': len(group_docs),
                                'method': f'alphabetical_force_depth_{depth}',
                                'parent_category': parent_category,
                                'document_ids': doc_ids
                            }
                        else:
                            break
                    
                    if len(subcategories) == num_groups:
                        best_split = subcategories
                
            return best_split or {}
                
        except Exception as e:
            pass
        
        return {}
    
    def _try_temporal_splitting(self, category_docs: pd.DataFrame, parent_category: str, depth: int, min_size_override: int) -> Dict:
        """Split based on temporal patterns"""
        try:
            sorted_docs = category_docs.sort_values('date')
            total_docs = len(sorted_docs)
            
            date_range = sorted_docs['date'].max() - sorted_docs['date'].min()
            
            if date_range.days > 30:
                sorted_docs['period'] = sorted_docs['date'].dt.to_period('M')
                period_groups = sorted_docs.groupby('period')
                
                valid_groups = {str(period): group for period, group in period_groups 
                              if len(group) >= min_size_override}
                
                if len(valid_groups) >= 2:
                    subcategories = {}
                    for period_name, group in valid_groups.items():
                        subcat_name = f"{parent_category}: {period_name}"
                        doc_ids = group['id'].tolist()
                        
                        subcategories[subcat_name] = {
                            'keywords': ['temporal', 'period', period_name.lower()],
                            'color': self.color_palette[(hash(subcat_name) % len(self.color_palette))],
                            'icon': '📅',
                            'size': len(group),
                            'method': f'temporal_depth_{depth}',
                            'parent_category': parent_category,
                            'document_ids': doc_ids
                        }
                    
                    return subcategories
            
            # Try chronological split
            max_groups = total_docs // min_size_override
            if max_groups >= 2:
                for num_groups in [2, 3]:
                    if num_groups > max_groups:
                        continue
                        
                    group_size = total_docs // num_groups
                    remainder = total_docs % num_groups
                    
                    subcategories = {}
                    current_idx = 0
                    
                    for i in range(num_groups):
                        current_group_size = group_size + (1 if i < remainder else 0)
                        
                        if i == num_groups - 1:
                            group_docs = sorted_docs.iloc[current_idx:]
                        else:
                            group_docs = sorted_docs.iloc[current_idx:current_idx + current_group_size]
                        
                        current_idx += current_group_size
                        
                        if len(group_docs) >= min_size_override:
                            if num_groups == 2:
                                period_name = "Earlier" if i == 0 else "Recent"
                            else:
                                period_name = ["Earlier", "Middle", "Recent"][i]
                            
                            subcat_name = f"{parent_category}: {period_name}"
                            doc_ids = group_docs['id'].tolist()
                            
                            subcategories[subcat_name] = {
                                'keywords': ['chronological', period_name.lower()],
                                'color': self.color_palette[(hash(subcat_name) % len(self.color_palette))],
                                'icon': '⏰',
                                'size': len(group_docs),
                                'method': f'chronological_depth_{depth}',
                                'parent_category': parent_category,
                                'document_ids': doc_ids
                            }
                        else:
                            break
                    
                    if len(subcategories) == num_groups:
                        return subcategories
                    
        except Exception as e:
            pass
        
        return {}
    
    def _generate_subcategory_name(self, parent_category: str, features: List[str], depth: int, cluster_id: int) -> str:
        """
        Generate subcategory name - default implementation
        Override in subclasses for domain-specific naming
        """
        clean_features = [f for f in features if len(f) > 2]
        
        if not clean_features:
            return f"{parent_category} - Subgroup {cluster_id + 1}"
        
        if len(clean_features) >= 2:
            return f"{clean_features[0].title()} & {clean_features[1].title()}"
        else:
            return f"{parent_category}: {clean_features[0].title()}"
    
    def _assign_categories_to_documents(self):
        """Assign discovered categories to documents"""
        if not self.categories:
            return
        
        self.df['category'] = 'Uncategorized'
        
        for category_name, category_data in self.categories.items():
            doc_indices = category_data.get('document_indices', [])
            
            for idx in doc_indices:
                if idx < len(self.df):
                    self.df.iloc[idx, self.df.columns.get_loc('category')] = category_name
    
    def _print_summary(self):
        """Print summary of loaded data and discovered categories"""
        print(f"✅ Loaded {len(self.df)} documents")
        print(f"📊 Categories discovered: {self.df['category'].nunique()}")
        print(f"📅 Date range: {self.df['date'].min().strftime('%Y-%m-%d')} to {self.df['date'].max().strftime('%Y-%m-%d')}")
        
        category_counts = self.df['category'].value_counts()
        uncategorized_pct = (category_counts.get('Uncategorized', 0) / len(self.df)) * 100
        print(f"📈 Uncategorized: {uncategorized_pct:.1f}%")
        
        print("\n🏆 Top discovered categories:")
        for i, (category, count) in enumerate(category_counts.head(10).items()):
            pct = (count / len(self.df)) * 100
            icon = self.categories.get(category, {}).get('icon', '📝')
            print(f"   {i+1}. {icon} {category}: {count} documents ({pct:.1f}%)")
    
    # Analysis and utility methods
    def search(self, query: str, case_sensitive: bool = False) -> pd.DataFrame:
        """Search documents for specific terms"""
        if self.df.empty:
            print("❌ No documents loaded")
            return pd.DataFrame()
        
        terms = [term.strip() for term in query.split(',')]
        
        def matches_query(doc):
            if not case_sensitive:
                doc = doc.lower()
                terms_to_check = [term.lower() for term in terms]
            else:
                terms_to_check = terms
            
            return any(term in doc for term in terms_to_check)
        
        results = self.df[self.df['document'].apply(matches_query)]
        
        print(f"🔍 Found {len(results)} matches for '{query}'")
        return results.sort_values('date', ascending=False)
    
    def category_summary(self) -> pd.DataFrame:
        """Get summary statistics by category"""
        if self.df.empty:
            return pd.DataFrame()
        
        summary = self.df.groupby('category').agg({
            'id': 'count',
            'word_count': 'mean',
            'char_count': 'mean',
            'date': ['min', 'max']
        }).round(2)
        
        summary.columns = ['Count', 'Avg Words', 'Avg Chars', 'First Document', 'Last Document']
        summary = summary.sort_values('Count', ascending=False)
        
        return summary
    
    def export_results(self, filename: str = "categorization_results.csv"):
        """Export analysis results to CSV"""
        if self.df.empty:
            print("❌ No data to export")
            return
        
        export_df = self.df.copy()
        export_df['category_keywords'] = export_df['category'].apply(
            lambda x: ', '.join(self.categories.get(x, {}).get('keywords', [])[:5])
        )
        export_df['category_parent'] = export_df['category'].apply(
            lambda x: self.categories.get(x, {}).get('parent_category', '')
        )
        
        export_df.to_csv(filename, index=False)
        print(f"💾 Exported {len(export_df)} document records to {filename}")
    
    def show_category_details(self):
        """Show detailed information about discovered categories"""
        if not self.categories:
            print("❌ No categories discovered yet")
            return
        
        print("🏷️  Discovered Category Details:")
        print("=" * 60)
        
        sorted_categories = sorted(self.categories.items(), 
                                 key=lambda x: x[1].get('size', 0), reverse=True)
        
        for category_name, category_data in sorted_categories:
            icon = category_data.get('icon', '📝')
            size = category_data.get('size', 'N/A')
            keywords = category_data.get('keywords', [])
            method = category_data.get('method', 'unknown')
            parent = category_data.get('parent_category', '')
            
            print(f"\n{icon} {category_name}")
            if parent:
                print(f"   Parent: {parent}")
            print(f"   Size: {size} documents")
            print(f"   Method: {method}")
            print(f"   Keywords: {', '.join(keywords[:8])}")
            print(f"   Color: {category_data.get('color', '#6B7280')}")
