import { useEffect, useRef, useState } from "react";

/** Generic data-fetch hook: runs `fetcher()` whenever `deps` change, tracks loading/error/data. */
export default function useFetch(fetcher, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const seq = useRef(0);

  useEffect(() => {
    let cancelled = false;
    const mySeq = ++seq.current;
    setLoading(true);
    setError(null);
    fetcher()
      .then((res) => {
        if (!cancelled && mySeq === seq.current) setData(res);
      })
      .catch((err) => {
        if (!cancelled && mySeq === seq.current) setError(err);
      })
      .finally(() => {
        if (!cancelled && mySeq === seq.current) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error };
}
