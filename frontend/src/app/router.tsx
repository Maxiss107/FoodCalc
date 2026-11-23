import { createBrowserRouter, Navigate } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import CatalogPage from '../features/catalog/pages/CatalogPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },
  {
    path: '/login',
    element: <div className="p-6 text-xl font-semibold">Экран входа</div>,
  },
  {
    path: '/register',
    element: <div className="p-6 text-xl font-semibold">Экран регистрации</div>,
  },
  {
    element: <MainLayout />,
    children: [
      {
        path: '/catalog',
        element: <CatalogPage />,
      },
      {
        path: '/recipes/new',
        element: <div className="text-2xl font-bold">Конструктор рецепта (новый)</div>,
      },
      {
        path: '/recipes/:id/edit',
        element: <div className="text-2xl font-bold">Конструктор рецепта (редактирование)</div>,
      },
      {
        path: '/orders',
        element: <div className="text-2xl font-bold">Доска заказов и план-факт</div>,
      },
      {
        path: '/purchases',
        element: <div className="text-2xl font-bold">Закупки</div>,
      },
    ],
  },
  {
    path: '*',
    element: <div className="p-6 text-xl text-red-600">404 — Страница не найдена</div>,
  },
]);
