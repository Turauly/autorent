import { initializeApp, getApps } from "firebase/app";
import {
  addDoc,
  collection,
  getDocs,
  getFirestore,
  orderBy,
  query,
  serverTimestamp
} from "firebase/firestore";
import type { TourRequest } from "./types";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};

function getRequiredValue(value: string | undefined, key: string) {
  if (!value?.trim()) {
    throw new Error(`Missing Firebase config: ${key}`);
  }
  return value;
}

function getFirestoreDb() {
  const app =
    getApps()[0] ??
    initializeApp({
      apiKey: getRequiredValue(firebaseConfig.apiKey, "VITE_FIREBASE_API_KEY"),
      authDomain: getRequiredValue(firebaseConfig.authDomain, "VITE_FIREBASE_AUTH_DOMAIN"),
      projectId: getRequiredValue(firebaseConfig.projectId, "VITE_FIREBASE_PROJECT_ID"),
      storageBucket: getRequiredValue(firebaseConfig.storageBucket, "VITE_FIREBASE_STORAGE_BUCKET"),
      messagingSenderId: getRequiredValue(
        firebaseConfig.messagingSenderId,
        "VITE_FIREBASE_MESSAGING_SENDER_ID"
      ),
      appId: getRequiredValue(firebaseConfig.appId, "VITE_FIREBASE_APP_ID")
    });

  return getFirestore(app);
}

export async function createTourRequest(payload: {
  packageId: string;
  packageTitle: string;
  route: string;
  days: number;
  price: number;
  userId: number;
  userEmail: string;
  userFullName?: string | null;
  userPhone?: string | null;
}) {
  const db = getFirestoreDb();
  await addDoc(collection(db, "tour_requests"), {
    ...payload,
    source: "frontend",
    status: "new",
    createdAt: serverTimestamp()
  });
}

export async function listTourRequests(): Promise<TourRequest[]> {
  const db = getFirestoreDb();
  const snapshot = await getDocs(query(collection(db, "tour_requests"), orderBy("createdAt", "desc")));
  return snapshot.docs.map((doc) => {
    const data = doc.data();
    const createdAt =
      typeof data.createdAt?.toDate === "function"
        ? data.createdAt.toDate().toISOString()
        : null;

    return {
      id: doc.id,
      packageId: String(data.packageId ?? ""),
      packageTitle: String(data.packageTitle ?? ""),
      route: String(data.route ?? ""),
      days: Number(data.days ?? 0),
      price: Number(data.price ?? 0),
      userId: Number(data.userId ?? 0),
      userEmail: String(data.userEmail ?? ""),
      userFullName: data.userFullName ? String(data.userFullName) : null,
      userPhone: data.userPhone ? String(data.userPhone) : null,
      source: String(data.source ?? ""),
      status: String(data.status ?? ""),
      createdAt
    };
  });
}
