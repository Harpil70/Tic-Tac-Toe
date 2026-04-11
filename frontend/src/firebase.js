/**
 * Firebase configuration.
 * Replace these with your actual Firebase project credentials.
 * 
 * HOW TO SET UP:
 * 1. Go to https://console.firebase.google.com/
 * 2. Click "Create a project" → Name it → Continue
 * 3. Go to Project Settings (gear icon) → General
 * 4. Scroll down to "Your apps" → Click Web icon (</>)
 * 5. Register app → Copy the firebaseConfig object
 * 6. Go to Authentication → Sign-in method → Enable "Email/Password" and "Google"
 * 7. Paste your config below
 */

import { initializeApp } from 'firebase/app';
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile,
  signOut,
  onAuthStateChanged,
} from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyAQ-zoQP4hMuRqJQXUd72s42O06oOEDfPw",
  authDomain: "geospatial-analyzer.firebaseapp.com",
  projectId: "geospatial-analyzer",
  storageBucket: "geospatial-analyzer.firebasestorage.app",
  messagingSenderId: "1069352809107",
  appId: "1:1069352809107:web:6b0b7fa9f32a8cbc5ad366"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export {
  auth,
  googleProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile,
  signOut,
  onAuthStateChanged,
};
